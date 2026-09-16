"""Authoritative immutable draft-revision service shared by HTTP and MCP."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import s3
from app.core.actor import Actor
from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleDraftRevision,
    DraftCommandReceipt,
)
from app.models.enums import (
    ArticleStatus,
    CompileStatus,
    DraftActorType,
    DraftRevisionReason,
)
from app.models.user import User
from app.schemas.article import ArticleUpdate, DocumentCommandPayload
from app.schemas.document2 import BLOCK_INSERTION_OPERATIONS
from app.services import butex_worker_client, compile_service

logger = logging.getLogger(__name__)

REVISION_RETENTION_LIMIT = 100

_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_FROZEN = HTTPException(
    status_code=409, detail="المخطوطة مجمّدة ولا يمكن تعديلها بعد التقديم."
)
_CONFLICT_MESSAGE = "وصل تعديل أحدث للمسودة؛ حُمّلت النسخة الأحدث من الخادم."
_COMMAND_ID_CONFLICT = HTTPException(
    status_code=409, detail="استُخدم معرّف الأمر نفسه مع محتوى مختلف."
)
_COMMAND_EXPIRED = HTTPException(
    status_code=409, detail="انتهت صلاحية نتيجة هذا الأمر القديمة؛ استخدم معرّف أمر جديداً."
)
_EDITABLE_STATUSES = {ArticleStatus.DRAFT, ArticleStatus.REVISION_REQUESTED}


def draft_storage_prefix(article_id: uuid.UUID | str) -> str:
    return f"articles/{article_id}/draft"


def draft_asset_prefix(article_id: uuid.UUID | str) -> str:
    return draft_storage_prefix(article_id)


def revision_storage_key(
    article_id: uuid.UUID | str, revision_id: uuid.UUID | str
) -> str:
    return f"{draft_storage_prefix(article_id)}/revisions/{revision_id}/document.json"


def preview_prefix(
    article_id: uuid.UUID | str,
    revision_id: uuid.UUID | str,
    compile_id: uuid.UUID | str,
) -> str:
    return f"{draft_storage_prefix(article_id)}/previews/{revision_id}/{compile_id}"


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def request_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def empty_document(title: str, abstract: str | None) -> dict[str, Any]:
    return {
        "node_type": "DocumentObject",
        "meta": {"title": title, "abstract": abstract or ""},
        "blocks": [],
    }


def assert_editable_author(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> Article:
    article = assert_author(db, article_id, actor)
    if article.status not in _EDITABLE_STATUSES:
        raise _FROZEN
    return article


def assert_author(db: Session, article_id: uuid.UUID, actor: Actor) -> Article:
    article = db.get(Article, article_id)
    link = db.scalar(
        select(ArticleAuthor).where(
            ArticleAuthor.article_id == article_id,
            ArticleAuthor.user_id == actor.user_id,
        )
    )
    if article is None or link is None:
        raise _NOT_FOUND
    return article


def get_current_revision(db: Session, article: Article) -> ArticleDraftRevision:
    if article.current_draft_revision_id is None:
        raise HTTPException(status_code=500, detail="لا توجد مسودة حالية للمقال.")
    revision = db.get(ArticleDraftRevision, article.current_draft_revision_id)
    if revision is None or revision.article_id != article.id:
        raise HTTPException(status_code=500, detail="تعذّر قراءة المسودة الحالية.")
    return revision


def read_document(revision: ArticleDraftRevision) -> dict[str, Any]:
    document = s3.get_json_key(revision.storage_key)
    if not isinstance(document, dict):
        raise HTTPException(status_code=503, detail="تعذّر قراءة المسودة المحفوظة.")
    return document


def revision_response(
    revision: ArticleDraftRevision, document: dict[str, Any]
) -> dict[str, Any]:
    return {
        "revision_id": revision.id,
        "revision_number": revision.revision_number,
        "document_hash": revision.document_hash,
        "actor_type": revision.actor_type,
        "reason": revision.reason,
        "created_at": revision.created_at,
        "restored_from_id": revision.restored_from_id,
        "restored_from_revision_number": revision.restored_from_revision_number,
        "document": document,
    }


def get_draft(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> dict[str, Any]:
    article = assert_editable_author(db, article_id, actor)
    revision = get_current_revision(db, article)
    return revision_response(revision, read_document(revision))


def get_outline(db: Session, article_id: uuid.UUID, actor: Actor) -> dict[str, Any]:
    draft = get_draft(db, article_id, actor)
    return {
        "revision_id": draft["revision_id"],
        "revision_number": draft["revision_number"],
        "outline": butex_worker_client.outline_document(draft["document"]),
    }


def get_blocks(db: Session, article_id: uuid.UUID, actor: Actor) -> dict[str, Any]:
    draft = get_draft(db, article_id, actor)
    blocks = draft["document"].get("blocks")
    return {
        "revision_id": draft["revision_id"],
        "revision_number": draft["revision_number"],
        "blocks": blocks if isinstance(blocks, list) else [],
    }


def _history_item(
    article: Article,
    revision: ArticleDraftRevision,
    created_by_name: str | None,
) -> dict[str, Any]:
    return {
        "revision_id": revision.id,
        "revision_number": revision.revision_number,
        "document_hash": revision.document_hash,
        "actor_type": revision.actor_type,
        "reason": revision.reason,
        "created_at": revision.created_at,
        "created_by": revision.created_by,
        "created_by_name": created_by_name,
        "restored_from_id": revision.restored_from_id,
        "restored_from_revision_number": revision.restored_from_revision_number,
        "is_current": revision.id == article.current_draft_revision_id,
    }


def list_revision_history(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> list[dict[str, Any]]:
    article = assert_author(db, article_id, actor)
    rows = db.execute(
        select(ArticleDraftRevision, User.full_name)
        .outerjoin(User, User.id == ArticleDraftRevision.created_by)
        .where(ArticleDraftRevision.article_id == article_id)
        .order_by(ArticleDraftRevision.revision_number.desc())
        .limit(REVISION_RETENTION_LIMIT)
    ).all()
    return [
        _history_item(article, revision, created_by_name)
        for revision, created_by_name in rows
    ]


def get_revision_history_detail(
    db: Session,
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    article = assert_author(db, article_id, actor)
    row = db.execute(
        select(ArticleDraftRevision, User.full_name)
        .outerjoin(User, User.id == ArticleDraftRevision.created_by)
        .where(
            ArticleDraftRevision.id == revision_id,
            ArticleDraftRevision.article_id == article_id,
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="المراجعة غير موجودة.")
    revision, created_by_name = row
    return {
        **_history_item(article, revision, created_by_name),
        "document": read_document(revision),
    }


def restore_revision(
    db: Session,
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    actor: Actor,
    base_revision: int,
) -> dict[str, Any]:
    if actor.auth_method != "human":
        raise HTTPException(status_code=403, detail="الاستعادة متاحة للمؤلفين فقط.")
    article = assert_editable_author(db, article_id, actor)
    article = db.scalar(
        select(Article)
        .where(Article.id == article.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if article is None or article.status not in _EDITABLE_STATUSES:
        raise _FROZEN
    target = db.get(ArticleDraftRevision, revision_id)
    if target is None or target.article_id != article_id:
        raise HTTPException(status_code=404, detail="المراجعة غير موجودة.")
    current = get_current_revision(db, article)
    if base_revision != current.revision_number:
        raise _conflict(current.revision_number)
    if target.id == current.id:
        raise HTTPException(status_code=409, detail="هذه هي المراجعة الحالية بالفعل.")
    document = read_document(target)
    revision, canonical, _ = create_revision(
        db,
        article_id=article_id,
        actor=actor,
        base_revision=base_revision,
        document=document,
        reason=DraftRevisionReason.RESTORE,
        restored_from_id=target.id,
        restored_from_revision_number=target.revision_number,
        force_revision=True,
    )
    return revision_response(revision, canonical)


def asset_is_referenced_by_history(
    db: Session, article_id: uuid.UUID, asset_id: str
) -> bool:
    revisions = list(
        db.scalars(
            select(ArticleDraftRevision)
            .where(ArticleDraftRevision.article_id == article_id)
            .order_by(ArticleDraftRevision.revision_number.desc())
            .limit(REVISION_RETENTION_LIMIT)
        ).all()
    )
    for revision in revisions:
        if revision.referenced_asset_ids is not None:
            if asset_id in revision.referenced_asset_ids:
                return True
            continue
        # Phase 1 rows predate the cached reference list. Fail closed if their
        # immutable snapshot cannot be read or exported.
        document = read_document(revision)
        _, raw_asset_ids = butex_worker_client.export_document(document)
        if asset_id in compile_service.validate_asset_keys(raw_asset_ids):
            return True
    return False


def document_metadata(document: dict[str, Any]) -> tuple[str, str | None]:
    meta = document.get("meta")
    if not isinstance(meta, dict):
        raise HTTPException(status_code=422, detail="بيانات المسودة غير صالحة.")
    raw_title = meta.get("title")
    raw_abstract = meta.get("abstract", "")
    if not isinstance(raw_title, str) or not raw_title.strip() or len(raw_title.strip()) > 500:
        raise HTTPException(status_code=422, detail="عنوان المقال في المسودة غير صالح.")
    if not isinstance(raw_abstract, str) or len(raw_abstract.strip()) > 5000:
        raise HTTPException(status_code=422, detail="ملخص المقال في المسودة غير صالح.")
    return raw_title.strip(), raw_abstract.strip() or None


def _assert_agent_authors_unchanged(
    actor: Actor,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    if actor.auth_method != "agent":
        return
    before_meta = before.get("meta") if isinstance(before.get("meta"), dict) else {}
    after_meta = after.get("meta") if isinstance(after.get("meta"), dict) else {}
    if before_meta.get("authors") != after_meta.get("authors"):
        raise HTTPException(status_code=403, detail="لا تسمح أدوات الوكيل بتعديل مؤلفي المقال.")


def _validate_referenced_assets(
    article_id: uuid.UUID, document: dict[str, Any]
) -> list[str]:
    _, asset_ids = butex_worker_client.export_document(document)
    validated = compile_service.validate_asset_keys(asset_ids)
    for asset_id in validated:
        try:
            s3.assert_exists(draft_asset_prefix(article_id), asset_id)
        except HTTPException as exc:
            if exc.status_code == 404:
                raise HTTPException(
                    status_code=422, detail="إحدى صور المقال المطلوبة غير موجودة."
                ) from exc
            raise
    return validated


def _conflict(current_revision: int) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "revision_conflict",
            "message": _CONFLICT_MESSAGE,
            "current_revision": current_revision,
        },
    )


def _receipt_result(
    db: Session,
    receipt: DraftCommandReceipt,
    expected_hash: str,
) -> tuple[ArticleDraftRevision, dict[str, Any], list[str]]:
    if receipt.request_hash != expected_hash:
        raise _COMMAND_ID_CONFLICT
    if receipt.result_revision_id is None:
        raise _COMMAND_EXPIRED
    revision = db.get(ArticleDraftRevision, receipt.result_revision_id)
    if revision is None:
        raise _COMMAND_EXPIRED
    return revision, read_document(revision), list(receipt.affected_block_ids or [])


def _prune_revisions(
    db: Session, article_id: uuid.UUID
) -> list[tuple[str, uuid.UUID]]:
    old = list(
        db.scalars(
            select(ArticleDraftRevision)
            .where(ArticleDraftRevision.article_id == article_id)
            .order_by(ArticleDraftRevision.revision_number.desc())
            .offset(REVISION_RETENTION_LIMIT)
        ).all()
    )
    snapshots = [(row.storage_key, row.id) for row in old]
    for row in old:
        db.delete(row)
    return snapshots


def create_revision(
    db: Session,
    *,
    article_id: uuid.UUID,
    actor: Actor,
    base_revision: int,
    document: dict[str, Any],
    reason: DraftRevisionReason,
    command_id: uuid.UUID | None = None,
    command_request_hash: str | None = None,
    affected_block_ids: list[str] | None = None,
    restored_from_id: uuid.UUID | None = None,
    restored_from_revision_number: int | None = None,
    force_revision: bool = False,
) -> tuple[ArticleDraftRevision, dict[str, Any], list[str]]:
    """Create N+1 exactly once, or return N for a canonical hash no-op."""
    article = assert_editable_author(db, article_id, actor)
    current = get_current_revision(db, article)
    current_document = read_document(current)

    if command_id is not None:
        existing = db.get(DraftCommandReceipt, command_id)
        if existing is not None:
            if existing.article_id != article_id:
                raise _COMMAND_ID_CONFLICT
            return _receipt_result(db, existing, command_request_hash or "")

    if base_revision != current.revision_number:
        raise _conflict(current.revision_number)
    if not isinstance(document, dict):
        raise HTTPException(status_code=422, detail="مستند المسودة غير صالح.")

    canonical = butex_worker_client.normalize_document(document)
    _assert_agent_authors_unchanged(actor, current_document, canonical)
    title, abstract = document_metadata(canonical)
    referenced_asset_ids = _validate_referenced_assets(article_id, canonical)
    document_hash = compile_service.hash_document(canonical)
    new_revision_id = uuid.uuid4()
    candidate_key = revision_storage_key(article_id, new_revision_id)
    candidate_written = force_revision or document_hash != current.document_hash
    if candidate_written:
        s3.put_json_key_immutable(candidate_key, canonical)

    locked_article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked_article is None or locked_article.status not in _EDITABLE_STATUSES:
        raise _FROZEN

    if command_id is not None:
        existing = db.get(DraftCommandReceipt, command_id)
        if existing is not None:
            if existing.article_id != article_id:
                raise _COMMAND_ID_CONFLICT
            return _receipt_result(db, existing, command_request_hash or "")

    locked_current = get_current_revision(db, locked_article)
    if locked_article.draft_revision_number != base_revision:
        raise _conflict(locked_article.draft_revision_number)

    affected = list(affected_block_ids or [])
    if document_hash == locked_current.document_hash and not force_revision:
        result = locked_current
        result_document = read_document(locked_current)
    else:
        result = ArticleDraftRevision(
            id=new_revision_id,
            article_id=article_id,
            revision_number=base_revision + 1,
            storage_key=candidate_key,
            document_hash=document_hash,
            created_by=actor.user_id,
            actor_type=(
                DraftActorType.AGENT if actor.auth_method == "agent" else DraftActorType.HUMAN
            ),
            reason=reason,
            restored_from_id=restored_from_id,
            restored_from_revision_number=restored_from_revision_number,
            referenced_asset_ids=referenced_asset_ids,
        )
        db.add(result)
        db.flush()
        locked_article.title = title
        locked_article.abstract = abstract
        locked_article.current_draft_revision_id = result.id
        locked_article.draft_revision_number = result.revision_number
        locked_article.updated_at = datetime.now(UTC)
        result_document = canonical

    if command_id is not None:
        db.add(
            DraftCommandReceipt(
                command_id=command_id,
                article_id=article_id,
                request_hash=command_request_hash or "",
                base_revision=base_revision,
                result_revision_id=result.id,
                result_revision_number=result.revision_number,
                affected_block_ids=affected,
            )
        )

    pruned_revisions = _prune_revisions(db, article_id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Command IDs are global. Two commands for different articles do not
        # share an article lock, so the receipt PK is the final arbiter.
        if command_id is not None:
            existing = db.get(DraftCommandReceipt, command_id)
            if existing is not None:
                if existing.article_id != article_id:
                    raise _COMMAND_ID_CONFLICT
                return _receipt_result(db, existing, command_request_hash or "")
        raise
    db.refresh(result)
    for key, revision_id in pruned_revisions:
        try:
            s3.delete_key(key)
        except Exception:
            logger.warning("Failed to delete pruned draft snapshot %s", key, exc_info=True)
        try:
            s3.delete_prefix(
                f"{draft_storage_prefix(article_id)}/previews/{revision_id}"
            )
        except Exception:
            logger.warning(
                "Failed to delete pruned draft previews for %s",
                revision_id,
                exc_info=True,
            )
    return result, result_document, affected


def put_draft(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    base_revision: int,
    document: Any,
) -> dict[str, Any]:
    revision, canonical, _ = create_revision(
        db,
        article_id=article_id,
        actor=actor,
        base_revision=base_revision,
        document=document,
        reason=DraftRevisionReason.AUTOSAVE,
    )
    return revision_response(revision, canonical)


def patch_metadata(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    payload: ArticleUpdate,
) -> Article:
    article = assert_editable_author(db, article_id, actor)
    current = get_current_revision(db, article)
    document = read_document(current)
    title = payload.title if "title" in payload.model_fields_set else article.title
    abstract = payload.abstract if "abstract" in payload.model_fields_set else article.abstract
    updated = butex_worker_client.apply_document_command(
        document,
        {"op": "update_document_meta", "title": title, "abstract": abstract or ""},
    )
    create_revision(
        db,
        article_id=article_id,
        actor=actor,
        base_revision=payload.base_revision,
        document=updated,
        reason=DraftRevisionReason.METADATA_EDIT,
    )
    db.refresh(article)
    return article


def _affected_block_ids(
    before: dict[str, Any], after: dict[str, Any], command: dict[str, Any]
) -> list[str]:
    for field in ("block_id", "list_id", "table_id"):
        target = command.get(field)
        if isinstance(target, str):
            return [target]
    before_ids = {
        block.get("id") for block in before.get("blocks", [])
        if isinstance(block, dict) and isinstance(block.get("id"), str)
    }
    return [
        block["id"] for block in after.get("blocks", [])
        if isinstance(block, dict)
        and isinstance(block.get("id"), str)
        and block["id"] not in before_ids
    ]


def apply_command(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    payload: DocumentCommandPayload,
) -> dict[str, Any]:
    article = assert_editable_author(db, article_id, actor)
    command_body = payload.command.model_dump(exclude_unset=True)
    body_hash = request_hash(
        {"base_revision": payload.base_revision, "command": command_body}
    )
    existing = db.get(DraftCommandReceipt, payload.command_id)
    if existing is not None:
        revision, document, affected = _receipt_result(db, existing, body_hash)
        return {
            "ok": True,
            **revision_response(revision, document),
            "affected_block_ids": affected,
        }

    current = get_current_revision(db, article)
    if payload.base_revision != current.revision_number:
        raise _conflict(current.revision_number)
    before = read_document(current)
    command = deepcopy(command_body)
    if command.get("op") in BLOCK_INSERTION_OPERATIONS:
        command["metadata"] = {
            "source": "agent" if actor.auth_method == "agent" else "user"
        }
    if actor.auth_method == "agent" and command.get("op") == "update_document_meta":
        if "authors" in command:
            raise HTTPException(status_code=403, detail="لا تسمح أدوات الوكيل بتعديل مؤلفي المقال.")
    after = butex_worker_client.apply_document_command(before, command)
    affected = _affected_block_ids(before, after, command)
    revision, canonical, affected = create_revision(
        db,
        article_id=article_id,
        actor=actor,
        base_revision=payload.base_revision,
        document=after,
        reason=DraftRevisionReason.AI_EDIT,
        command_id=payload.command_id,
        command_request_hash=body_hash,
        affected_block_ids=affected,
    )
    return {
        "ok": True,
        **revision_response(revision, canonical),
        "affected_block_ids": affected,
    }


def compile_status(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> dict[str, Any]:
    article = assert_editable_author(db, article_id, actor)
    revision = get_current_revision(db, article)
    error = None
    if revision.compile_error_code and revision.compile_error_message:
        error = {
            "code": revision.compile_error_code,
            "message": revision.compile_error_message,
        }
    return {
        "status": revision.compile_status,
        "compile_id": revision.active_compile_id,
        "revision_id": revision.id,
        "revision_number": revision.revision_number,
        "pdf_ready": (
            revision.compile_status == CompileStatus.SUCCESS
            and revision.active_compile_id is not None
            and revision.compiled_at is not None
        ),
        "error": error,
    }


def prepare_compile(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    article = assert_editable_author(db, article_id, actor)
    revision = get_current_revision(db, article)
    document = read_document(revision)
    latex, asset_ids = butex_worker_client.export_document(document)
    asset_ids = compile_service.validate_asset_keys(asset_ids)
    for asset_id in asset_ids:
        try:
            s3.assert_exists(draft_asset_prefix(article_id), asset_id)
        except HTTPException as exc:
            if exc.status_code == 404:
                raise HTTPException(
                    status_code=422, detail="إحدى صور المقال المطلوبة غير موجودة."
                ) from exc
            raise
    revision, compile_id = compile_service.begin_compile(db, revision)
    return compile_status(db, article_id, actor), (
        revision.id,
        compile_id,
        latex,
        asset_ids,
    )


def get_current_pdf(db: Session, article_id: uuid.UUID, actor: Actor) -> bytes:
    article = assert_editable_author(db, article_id, actor)
    revision = get_current_revision(db, article)
    compile_service.assert_fresh_preview_for_submit(revision)
    assert revision.active_compile_id is not None
    return compile_service.get_compiled_pdf(
        preview_prefix(article_id, revision.id, revision.active_compile_id)
    )


def get_current_compile_log(db: Session, article_id: uuid.UUID, actor: Actor) -> str:
    article = assert_editable_author(db, article_id, actor)
    revision = get_current_revision(db, article)
    if revision.active_compile_id is None:
        raise HTTPException(status_code=404, detail="لا يوجد سجل معاينة.")
    return compile_service.get_compile_log(
        preview_prefix(article_id, revision.id, revision.active_compile_id)
    )
