"""Compile one exact immutable draft revision into one immutable preview attempt."""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import re
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import s3
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.article import ArticleDraftRevision
from app.models.enums import CompileStatus

logger = logging.getLogger(__name__)
_COMPILER_TIMEOUT = 200
_ASSET_KEY_RE = re.compile(
    r"^assets/[A-Za-z0-9._-]+\.(?:jpg|jpeg|png|pdf|gif|webp)$", re.IGNORECASE
)
_MAX_ASSETS = 50
_COMPILER_UNAVAILABLE = HTTPException(
    status_code=503, detail="خدمة إنشاء ملفّ المعاينة غير متاحة حالياً."
)
_ALREADY_PROCESSING = HTTPException(
    status_code=409, detail="إنشاء ملفّ المعاينة قيد التنفيذ بالفعل."
)
_STALE_PREVIEW = HTTPException(
    status_code=409, detail="يجب إنشاء ملفّ معاينة حديث بعد آخر تعديل قبل إرسال المقال."
)


def compiler_is_configured() -> bool:
    return bool((settings.compiler_url or "").strip())


def hash_document(document: object) -> str:
    payload = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_asset_keys(keys: list[str]) -> list[str]:
    if len(keys) > _MAX_ASSETS:
        raise HTTPException(status_code=400, detail="يتجاوز عدد الصور الحد المسموح.")
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in keys:
        key = raw.strip()
        if not _ASSET_KEY_RE.match(key) or ".." in key:
            raise HTTPException(status_code=400, detail="يتضمن المقال مرجع صورة غير صالح.")
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
    try:
        with httpx.Client(timeout=_COMPILER_TIMEOUT) as client:
            if assets:
                response = client.post(
                    f"{base}/xelatex/render",
                    data={"tex": tex, "job_name": job_name},
                    files=[
                        ("asset", (key, body, content_type))
                        for key, body, content_type in assets
                    ],
                )
            else:
                response = client.post(
                    f"{base}/xelatex/render",
                    json={"tex": tex, "job_name": job_name},
                    headers={"Content-Type": "application/json"},
                )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503, detail="تعذّر الاتصال بخدمة إنشاء المعاينة."
        ) from exc
    if response.status_code == 200:
        return response.content
    raise HTTPException(status_code=502, detail=response.text[:4000] or "فشل التجميع.")


def _is_active(db: Session, revision: ArticleDraftRevision, compile_id: uuid.UUID) -> bool:
    db.refresh(revision)
    return revision.active_compile_id == compile_id


def begin_compile(
    db: Session, revision: ArticleDraftRevision
) -> tuple[ArticleDraftRevision, uuid.UUID]:
    if not compiler_is_configured():
        raise _COMPILER_UNAVAILABLE
    locked = db.get(
        ArticleDraftRevision,
        revision.id,
        with_for_update=True,
        populate_existing=True,
    )
    if locked is None:
        raise HTTPException(status_code=404, detail="المسودة غير موجودة.")
    if locked.compile_status == CompileStatus.PROCESSING:
        raise _ALREADY_PROCESSING
    compile_id = uuid.uuid4()
    locked.active_compile_id = compile_id
    locked.compile_status = CompileStatus.PROCESSING
    locked.compile_error_code = None
    locked.compile_error_message = None
    locked.compiled_at = None
    db.commit()
    db.refresh(locked)
    return locked, compile_id


def record_compile_failure(
    db: Session,
    revision: ArticleDraftRevision,
    compile_id: uuid.UUID,
    *,
    code: str,
    message: str,
) -> None:
    if _is_active(db, revision, compile_id):
        revision.compile_status = CompileStatus.FAILED
        revision.compile_error_code = code[:100]
        revision.compile_error_message = message[:2000]
        revision.compiled_at = None
        db.commit()


def _attempt_prefix(revision: ArticleDraftRevision, compile_id: uuid.UUID) -> str:
    return f"articles/{revision.article_id}/draft/previews/{revision.id}/{compile_id}"


def _store_log(revision: ArticleDraftRevision, compile_id: uuid.UUID, text: str) -> None:
    try:
        s3.put_bytes_key_immutable(
            f"{_attempt_prefix(revision, compile_id)}/{s3.COMPILE_LOG}",
            text.encode("utf-8"),
            "text/plain; charset=utf-8",
        )
    except Exception:
        logger.warning("Failed to store compile log", exc_info=True)


def compile_revision(
    db: Session,
    revision_id: uuid.UUID,
    compile_id: uuid.UUID,
    latex: str,
    asset_keys: list[str],
) -> None:
    revision = db.get(ArticleDraftRevision, revision_id)
    if revision is None or not _is_active(db, revision, compile_id):
        return
    try:
        assets: list[tuple[str, bytes, str]] = []
        draft_prefix = f"articles/{revision.article_id}/draft"
        for key in validate_asset_keys(asset_keys):
            body, content_type = s3.get_bytes(draft_prefix, key)
            assets.append((key, body, content_type or _content_type_for_key(key)))
        pdf = _call_compiler(
            latex,
            f"article-draft-{revision.revision_number}-{revision.id.hex[:8]}",
            assets,
        )
        if not _is_active(db, revision, compile_id):
            return
        s3.put_bytes_key_immutable(
            f"{_attempt_prefix(revision, compile_id)}/{s3.COMPILED_PDF}",
            pdf,
            "application/pdf",
        )
        if not _is_active(db, revision, compile_id):
            return
        revision.compile_status = CompileStatus.SUCCESS
        revision.compile_error_code = None
        revision.compile_error_message = None
        revision.compiled_at = datetime.now(UTC)
        db.commit()
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        logger.warning("Draft compile failed for %s: %s", revision_id, detail)
        if _is_active(db, revision, compile_id):
            revision.compile_status = CompileStatus.FAILED
            revision.compile_error_code = "compile_failed"
            revision.compile_error_message = "تعذّر إنشاء ملفّ المعاينة. راجع المقال ثم حاول مجدداً."
            revision.compiled_at = None
            db.commit()
            _store_log(revision, compile_id, detail)
    except Exception:
        logger.exception("Unexpected draft compile failure for %s", revision_id)
        if _is_active(db, revision, compile_id):
            revision.compile_status = CompileStatus.FAILED
            revision.compile_error_code = "compile_failed"
            revision.compile_error_message = "تعذّر إنشاء ملفّ المعاينة. حاول مجدداً."
            revision.compiled_at = None
            db.commit()
            _store_log(revision, compile_id, "خطأ غير متوقع أثناء التجميع.")


def schedule_compile(
    revision_id: uuid.UUID,
    compile_id: uuid.UUID,
    latex: str,
    asset_keys: list[str],
) -> None:
    db = SessionLocal()
    try:
        compile_revision(db, revision_id, compile_id, latex, asset_keys)
    finally:
        db.close()


def assert_fresh_preview_for_submit(revision: ArticleDraftRevision) -> None:
    if (
        revision.compile_status != CompileStatus.SUCCESS
        or revision.active_compile_id is None
        or revision.compiled_at is None
    ):
        raise _STALE_PREVIEW


def get_compiled_pdf(storage_prefix: str) -> bytes:
    body, _ = s3.get_bytes(storage_prefix, s3.COMPILED_PDF)
    return body


def get_compile_log(storage_prefix: str) -> str:
    body, _ = s3.get_bytes(storage_prefix, s3.COMPILE_LOG)
    return body.decode("utf-8", errors="replace")
