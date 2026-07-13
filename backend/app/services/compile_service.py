"""تجميع BuTeX → PDF عبر المترجم المشترك (XeLaTeX) وتخزين compiled.pdf في S3."""

from __future__ import annotations

import json
import logging
import mimetypes
import re
import subprocess
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import s3
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.article import ArticleVersion
from app.models.enums import CompileStatus

logger = logging.getLogger(__name__)

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "document2_latex.mjs"
_NODE_TIMEOUT = 60
_COMPILER_TIMEOUT = 200
_ASSET_KEY_RE = re.compile(
    r"^assets/[A-Za-z0-9._-]+\.(?:jpg|jpeg|png|pdf|gif|webp)$",
    re.IGNORECASE,
)
_MAX_ASSETS = 50

_COMPILER_UNAVAILABLE = HTTPException(
    status_code=503,
    detail="خدمة التجميع غير مُهيّأة على الخادم.",
)
_ALREADY_PROCESSING = HTTPException(
    status_code=409,
    detail="تجميع قيد التنفيذ بالفعل.",
)
_NO_DOCUMENT = HTTPException(
    status_code=400,
    detail="لا توجد مخطوطة محفوظة للتجميع.",
)


def _normalize_asset_key(raw: str | None) -> str | None:
    if not raw:
        return None
    trimmed = raw.strip()
    if not trimmed or trimmed.startswith(("http://", "https://", "blob:")):
        return None
    if not trimmed.startswith("assets/"):
        return None
    name = trimmed[len("assets/") :]
    if not name or "/" in name or ".." in name:
        return None
    key = f"assets/{name}"
    if not _ASSET_KEY_RE.match(key):
        return None
    return key


def collect_asset_keys(document: object) -> list[str]:
    """يجمع مفاتيح assets/... من كتل \\includegraphics في document.json."""
    keys: set[str] = set()

    def visit_blocks(blocks: object) -> None:
        if not isinstance(blocks, list):
            return
        for block in blocks:
            if not isinstance(block, dict):
                continue
            command = block.get("command")
            kind = block.get("kind")
            if kind == "image" or command == "\\includegraphics":
                for candidate in (
                    block.get("asset_id"),
                    block.get("assetId"),
                    block.get("value"),
                    block.get("src"),
                ):
                    if isinstance(candidate, str):
                        key = _normalize_asset_key(candidate)
                        if key:
                            keys.add(key)
            items = block.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        visit_blocks(item.get("blocks"))

    if isinstance(document, dict):
        visit_blocks(document.get("blocks"))
    return sorted(keys)


def document_to_latex(document: object) -> str:
    """يستدعي سكربت Node لتصدير XeLaTeX كامل من document.json."""
    if not _SCRIPT.is_file():
        raise HTTPException(
            status_code=503,
            detail="سكربت تصدير LaTeX غير موجود على الخادم.",
        )
    payload = json.dumps(document, ensure_ascii=False).encode("utf-8")
    try:
        result = subprocess.run(
            ["node", str(_SCRIPT)],
            input=payload,
            capture_output=True,
            timeout=_NODE_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Node.js غير متاح على الخادم لتصدير المخطوطة.",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="انتهت مهلة تصدير المخطوطة إلى LaTeX.",
        ) from exc

    if result.returncode != 0:
        err = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        logger.error("document2_latex failed: %s", err)
        raise HTTPException(
            status_code=500,
            detail=err or "تعذّر تصدير المخطوطة إلى LaTeX.",
        )
    tex = (result.stdout or b"").decode("utf-8")
    if not tex.strip():
        raise HTTPException(status_code=500, detail="ناتج تصدير LaTeX فارغ.")
    return tex


def _content_type_for_key(key: str) -> str:
    guessed, _ = mimetypes.guess_type(key)
    return guessed or "application/octet-stream"


def _call_compiler(tex: str, job_name: str, assets: list[tuple[str, bytes, str]]) -> bytes:
    base = (settings.compiler_url or "").rstrip("/")
    if not base:
        raise _COMPILER_UNAVAILABLE

    url = f"{base}/xelatex/render"
    try:
        with httpx.Client(timeout=_COMPILER_TIMEOUT) as client:
            if assets:
                files: list[tuple[str, tuple[str, bytes, str]]] = [
                    ("asset", (key, body, content_type))
                    for key, body, content_type in assets
                ]
                data = {"tex": tex, "job_name": job_name}
                response = client.post(url, data=data, files=files)
            else:
                response = client.post(
                    url,
                    json={"tex": tex, "job_name": job_name},
                    headers={"Content-Type": "application/json"},
                )
    except httpx.HTTPError as exc:
        logger.exception("compiler request failed")
        raise HTTPException(
            status_code=503,
            detail="تعذّر الاتصال بخدمة التجميع.",
        ) from exc

    if response.status_code == 200:
        return response.content

    detail: str
    try:
        payload = response.json()
        if isinstance(payload, dict):
            raw = payload.get("detail", payload)
            if isinstance(raw, dict) and "log_tail" in raw:
                detail = str(raw.get("message") or raw.get("detail") or raw)
                log_tail = str(raw.get("log_tail") or "")
                if log_tail:
                    detail = f"{detail}\n\n{log_tail}"
            else:
                detail = str(raw)
        else:
            detail = str(payload)
    except Exception:
        detail = response.text[:4000] or f"compiler HTTP {response.status_code}"

    raise HTTPException(status_code=502, detail=detail)


def _mark_status(db: Session, version: ArticleVersion, status: CompileStatus) -> None:
    version.compile_status = status
    db.commit()


def _store_log(storage_prefix: str, text: str) -> None:
    try:
        s3.put_bytes(
            storage_prefix,
            s3.COMPILE_LOG,
            text.encode("utf-8"),
            "text/plain; charset=utf-8",
        )
    except Exception:
        logger.exception("failed to store compile.log")


def compile_version(db: Session, version: ArticleVersion) -> None:
    """يجمّع إصدارًا واحدًا ويحدّث compile_status + يخزّن compiled.pdf."""
    if not (settings.compiler_url or "").strip():
        _mark_status(db, version, CompileStatus.FAILED)
        _store_log(version.storage_prefix, "COMPILER_URL غير مُعدّ.")
        return

    document = s3.get_json(version.storage_prefix)
    if document is None:
        _mark_status(db, version, CompileStatus.FAILED)
        _store_log(version.storage_prefix, "document.json غير موجود.")
        return

    try:
        tex = document_to_latex(document)
        keys = collect_asset_keys(document)
        if len(keys) > _MAX_ASSETS:
            raise HTTPException(
                status_code=400,
                detail=f"عدد الصور يتجاوز الحد المسموح ({_MAX_ASSETS}).",
            )

        assets: list[tuple[str, bytes, str]] = []
        for key in keys:
            try:
                body, content_type = s3.get_bytes(version.storage_prefix, key)
            except HTTPException as exc:
                if exc.status_code == 404:
                    raise HTTPException(
                        status_code=400,
                        detail=f"صورة مفقودة في التخزين: {key}",
                    ) from exc
                raise
            assets.append((key, body, content_type or _content_type_for_key(key)))

        job_name = f"article-v{version.version_number}-{version.id.hex[:8]}"
        pdf = _call_compiler(tex, job_name, assets)
        s3.put_bytes(
            version.storage_prefix,
            s3.COMPILED_PDF,
            pdf,
            "application/pdf",
        )
        _mark_status(db, version, CompileStatus.SUCCESS)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        logger.warning("compile failed for %s: %s", version.id, detail)
        _mark_status(db, version, CompileStatus.FAILED)
        _store_log(version.storage_prefix, detail)
    except Exception:
        logger.exception("unexpected compile failure for %s", version.id)
        _mark_status(db, version, CompileStatus.FAILED)
        _store_log(version.storage_prefix, "خطأ غير متوقع أثناء التجميع.")


def schedule_compile(version_id: uuid.UUID) -> None:
    """يُستدعى من BackgroundTasks — جلسة DB مستقلة."""
    db = SessionLocal()
    try:
        version = db.get(ArticleVersion, version_id)
        if version is None:
            logger.error("schedule_compile: version %s not found", version_id)
            return
        compile_version(db, version)
    finally:
        db.close()


def begin_compile(db: Session, version: ArticleVersion) -> ArticleVersion:
    """يضع processing ويرفض إن كان التجميع جاريًا. يُستدعى قبل BackgroundTasks."""
    if not (settings.compiler_url or "").strip():
        raise _COMPILER_UNAVAILABLE

    db.refresh(version)
    if version.compile_status == CompileStatus.PROCESSING:
        raise _ALREADY_PROCESSING

    # تحقق مبكر من وجود مستند
    document = s3.get_json(version.storage_prefix)
    if document is None:
        raise _NO_DOCUMENT

    version.compile_status = CompileStatus.PROCESSING
    db.commit()
    db.refresh(version)
    return version


def get_compiled_pdf(storage_prefix: str) -> bytes:
    body, _ = s3.get_bytes(storage_prefix, s3.COMPILED_PDF)
    return body
