"""تجميع PDF عبر المترجم المشترك — الـ LaTeX يأتي من الواجهة كـ string."""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import re
import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import s3
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.article import ArticleVersion
from app.models.enums import CompileStatus

logger = logging.getLogger(__name__)

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
    detail="إنشاء ملفّ المعاينة قيد التنفيذ بالفعل.",
)
_NO_DOCUMENT = HTTPException(
    status_code=400,
    detail="لا توجد مخطوطة محفوظة للتجميع.",
)
_HASH_MISMATCH = HTTPException(
    status_code=409,
    detail="احفظ المخطوطة ثم أعد إنشاء ملفّ المعاينة.",
)
_STALE_PREVIEW = HTTPException(
    status_code=409,
    detail="يجب إنشاء ملفّ معاينة حديث بعد آخر تعديل قبل إرسال المقال.",
)


def hash_document(document: object) -> str:
    """SHA-256 لـ JSON المعياري (مفاتيح مرتّبة، بدون مسافات زائدة)."""
    payload = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_document_hash(storage_prefix: str) -> str | None:
    document = s3.get_json(storage_prefix)
    if document is None:
        return None
    return hash_document(document)


def validate_asset_keys(keys: list[str]) -> list[str]:
    if len(keys) > _MAX_ASSETS:
        raise HTTPException(
            status_code=400,
            detail=f"عدد الصور يتجاوز الحد المسموح ({_MAX_ASSETS}).",
        )
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in keys:
        key = raw.strip()
        if not _ASSET_KEY_RE.match(key) or ".." in key:
            raise HTTPException(
                status_code=400,
                detail=f"مفتاح صورة غير صالح: {raw}",
            )
        if key not in seen:
            seen.add(key)
            cleaned.append(key)
    return cleaned


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


def _is_active(db: Session, version: ArticleVersion, compile_id: uuid.UUID) -> bool:
    db.refresh(version)
    return version.active_compile_id == compile_id


def compile_version(
    db: Session,
    version_id: uuid.UUID,
    compile_id: uuid.UUID,
    latex: str,
    asset_keys: list[str],
    document_hash: str,
) -> None:
    version = db.get(ArticleVersion, version_id)
    if version is None:
        logger.error("compile_version: version %s not found", version_id)
        return

    if not _is_active(db, version, compile_id):
        logger.info("skip stale compile %s for version %s", compile_id, version_id)
        return

    if not (settings.compiler_url or "").strip():
        if _is_active(db, version, compile_id):
            version.compile_status = CompileStatus.FAILED
            db.commit()
            _store_log(version.storage_prefix, "COMPILER_URL غير مُعدّ.")
        return

    try:
        keys = validate_asset_keys(asset_keys)
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
        pdf = _call_compiler(latex, job_name, assets)

        if not _is_active(db, version, compile_id):
            logger.info(
                "discard PDF for superseded compile %s version %s",
                compile_id,
                version_id,
            )
            return

        s3.put_bytes(
            version.storage_prefix,
            s3.COMPILED_PDF,
            pdf,
            "application/pdf",
        )
        version.compile_status = CompileStatus.SUCCESS
        version.compiled_document_hash = document_hash
        db.commit()
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        logger.warning("compile failed for %s: %s", version_id, detail)
        if _is_active(db, version, compile_id):
            version.compile_status = CompileStatus.FAILED
            db.commit()
            _store_log(version.storage_prefix, detail)
    except Exception:
        logger.exception("unexpected compile failure for %s", version_id)
        if _is_active(db, version, compile_id):
            version.compile_status = CompileStatus.FAILED
            db.commit()
            _store_log(version.storage_prefix, "خطأ غير متوقع أثناء التجميع.")


def schedule_compile(
    version_id: uuid.UUID,
    compile_id: uuid.UUID,
    latex: str,
    asset_keys: list[str],
    document_hash: str,
) -> None:
    """يُستدعى من BackgroundTasks — جلسة DB مستقلة؛ latex في الذاكرة فقط."""
    db = SessionLocal()
    try:
        compile_version(
            db, version_id, compile_id, latex, asset_keys, document_hash
        )
    finally:
        db.close()


def begin_compile(
    db: Session,
    version: ArticleVersion,
    document_hash: str,
) -> tuple[ArticleVersion, uuid.UUID]:
    """يضع processing + active_compile_id بعد التحقق من hash المستند."""
    if not (settings.compiler_url or "").strip():
        raise _COMPILER_UNAVAILABLE

    db.refresh(version)
    if version.compile_status == CompileStatus.PROCESSING:
        raise _ALREADY_PROCESSING

    current = current_document_hash(version.storage_prefix)
    if current is None:
        raise _NO_DOCUMENT
    if current != document_hash:
        raise _HASH_MISMATCH

    compile_id = uuid.uuid4()
    version.active_compile_id = compile_id
    version.compile_status = CompileStatus.PROCESSING
    db.commit()
    db.refresh(version)
    return version, compile_id


def assert_fresh_preview_for_submit(version: ArticleVersion) -> None:
    """يرفض التقديم إن لم يكن ملفّ المعاينة ناجحًا ومطابقًا للمستند الحالي."""
    if version.compile_status != CompileStatus.SUCCESS:
        raise _STALE_PREVIEW
    current = current_document_hash(version.storage_prefix)
    if current is None or version.compiled_document_hash != current:
        raise _STALE_PREVIEW


def get_compiled_pdf(storage_prefix: str) -> bytes:
    body, _ = s3.get_bytes(storage_prefix, s3.COMPILED_PDF)
    return body


def get_compile_log(storage_prefix: str) -> str:
    """يقرأ compile.log من التخزين — يرفع 404 إن غاب."""
    body, _ = s3.get_bytes(storage_prefix, s3.COMPILE_LOG)
    return body.decode("utf-8", errors="replace")
