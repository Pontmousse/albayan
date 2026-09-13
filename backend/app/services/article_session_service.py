"""Shared article editing sessions for humans and agents."""

from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import s3
from app.core.actor import Actor
from app.models.article import Article, ArticleSession, ArticleVersion
from app.models.enums import CompileStatus
from app.schemas.article import ArticleUpdate, DocumentCommandPayload
from app.schemas.document2 import BLOCK_INSERTION_OPERATIONS
from app.services import article_service, butex_worker_client, compile_service

SESSION_PREFIX = "session"
SESSION_DOCUMENT = f"{SESSION_PREFIX}/document.json"
SESSION_META = f"{SESSION_PREFIX}/meta.json"
SESSION_COMMANDS_PREFIX = f"{SESSION_PREFIX}/commands"

_CONFLICT = HTTPException(
    status_code=409,
    detail="تغيّرت جلسة التحرير؛ أعد تحميلها ثم حاول مرة أخرى.",
)
_COMMAND_ID_CONFLICT = HTTPException(
    status_code=409,
    detail="استُخدم command_id نفسه مع طلب مختلف.",
)


def session_storage_prefix(article_id: uuid.UUID | str) -> str:
    return f"articles/{article_id}/"


def _empty_document(article: Article) -> dict[str, Any]:
    return {
        "node_type": "DocumentObject",
        "meta": {
            "title": article.title,
            "abstract": article.abstract or "",
        },
        "blocks": [],
    }


def _synchronize_document_metadata(
    document: dict[str, Any],
    *,
    title: str,
    abstract: str | None,
) -> dict[str, Any]:
    """Apply authoritative host metadata through the worker's typed command path."""
    return butex_worker_client.apply_document_command(
        document,
        {
            "op": "update_document_meta",
            "title": title,
            "abstract": abstract or "",
        },
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _command_key(command_id: uuid.UUID) -> str:
    return f"{SESSION_COMMANDS_PREFIX}/{command_id}.json"


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _request_hash(payload: DocumentCommandPayload) -> str:
    body = {
        "base_revision": payload.base_revision,
        "command": payload.command.model_dump(exclude_unset=True),
    }
    return hashlib.sha256(_stable_json(body).encode("utf-8")).hexdigest()


def _meta(session: ArticleSession) -> dict[str, Any]:
    return {
        "revision": session.revision,
        "last_saved_revision": session.last_saved_revision,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "updated_by": str(session.updated_by) if session.updated_by else None,
        "article_version_id": str(session.article_version_id),
    }


def _write_meta(article_id: uuid.UUID, session: ArticleSession) -> None:
    s3.put_json_at(
        session_storage_prefix(article_id),
        f"{SESSION_PREFIX}/meta.json",
        _meta(session),
    )


def _session_document(article_id: uuid.UUID) -> dict[str, Any]:
    document = s3.get_json_at(session_storage_prefix(article_id), SESSION_DOCUMENT)
    if not isinstance(document, dict):
        raise HTTPException(status_code=404, detail="جلسة التحرير غير موجودة.")
    return document


def _command_record(
    article_id: uuid.UUID,
    command_id: uuid.UUID,
) -> dict[str, Any] | None:
    record = s3.get_json_at(session_storage_prefix(article_id), _command_key(command_id))
    return record if isinstance(record, dict) else None


def _write_command_record(
    article_id: uuid.UUID,
    command_id: uuid.UUID,
    record: dict[str, Any],
) -> None:
    s3.put_json_at(session_storage_prefix(article_id), _command_key(command_id), record)


def _affected_block_ids(
    before: dict[str, Any],
    after: dict[str, Any],
    command: dict[str, Any],
) -> list[str]:
    for target_field in ("block_id", "list_id", "table_id"):
        target_id = command.get(target_field)
        if isinstance(target_id, str):
            return [target_id]

    field_id = command.get("field_id")
    if isinstance(field_id, str):
        owner_id = _block_id_for_field(before, field_id) or _block_id_for_field(
            after, field_id
        )
        return [owner_id] if owner_id else []

    before_ids = {
        block.get("id")
        for block in before.get("blocks", [])
        if isinstance(block, dict) and isinstance(block.get("id"), str)
    }
    after_ids = [
        block.get("id")
        for block in after.get("blocks", [])
        if isinstance(block, dict) and isinstance(block.get("id"), str)
    ]
    return [block_id for block_id in after_ids if block_id not in before_ids]


def _block_id_for_field(document: dict[str, Any], field_id: str) -> str | None:
    def inline_ids_match(value: object) -> bool:
        return isinstance(value, dict) and value.get("field_id") == field_id

    def find_in_block(block: object) -> str | None:
        if not isinstance(block, dict):
            return None
        block_id = block.get("id")
        owner_id = block_id if isinstance(block_id, str) else None

        if inline_ids_match(block.get("inline_ids")):
            return owner_id

        cell_inline_ids = block.get("cell_inline_ids")
        if isinstance(cell_inline_ids, list):
            for row in cell_inline_ids:
                if isinstance(row, list) and any(
                    inline_ids_match(cell) for cell in row
                ):
                    return owner_id

        items = block.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                if inline_ids_match(item.get("inline_ids")):
                    return owner_id
                nested_blocks = item.get("blocks")
                if isinstance(nested_blocks, list):
                    for nested_block in nested_blocks:
                        nested_owner = find_in_block(nested_block)
                        if nested_owner:
                            return nested_owner
        return None

    blocks = document.get("blocks")
    if not isinstance(blocks, list):
        return None
    for block in blocks:
        owner_id = find_in_block(block)
        if owner_id:
            return owner_id
    return None


def _worker_command(
    payload: DocumentCommandPayload,
    actor: Actor,
) -> dict[str, Any]:
    command = deepcopy(payload.command.model_dump(exclude_unset=True))
    if command.get("op") in BLOCK_INSERTION_OPERATIONS:
        source = "agent" if actor.auth_method == "agent" else "user"
        command["metadata"] = {"source": source}
    return command


def _select_current_session(db: Session, article_id: uuid.UUID) -> ArticleSession | None:
    return db.scalar(select(ArticleSession).where(ArticleSession.article_id == article_id))


def _lock_current_session(db: Session, article_id: uuid.UUID) -> ArticleSession | None:
    return db.scalar(
        select(ArticleSession)
        .where(ArticleSession.article_id == article_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _lock_metadata_rows(
    db: Session,
    article_id: uuid.UUID,
) -> tuple[Article, ArticleVersion]:
    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    version = db.scalar(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article_id)
        .order_by(ArticleVersion.version_number.desc())
        .limit(1)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not article or not version:
        raise HTTPException(status_code=404, detail="المقال غير موجود.")
    article_service.assert_draft(version)
    return article, version


def _current_draft_article_and_version(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> tuple[Article, ArticleVersion]:
    article = article_service.assert_is_author(db, article_id, actor.user_id)
    version = article_service.current_version(db, article_id)
    article_service.assert_draft(version)
    return article, version


def get_or_create_session(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> tuple[ArticleSession, dict[str, Any]]:
    article, version = _current_draft_article_and_version(db, article_id, actor)
    session = _select_current_session(db, article_id)
    if session and session.article_version_id == version.id:
        return session, _session_document(article_id)

    # Serialize first-session creation with metadata updates. Re-read both the
    # session and authoritative rows after acquiring their locks so a session
    # created while this request was waiting cannot be duplicated or seeded
    # from stale Article metadata.
    session = _lock_current_session(db, article_id)
    article, version = _lock_metadata_rows(db, article_id)
    session = _lock_current_session(db, article_id)
    if session and session.article_version_id == version.id:
        return session, _session_document(article_id)

    if session:
        s3.delete_prefix(f"{session_storage_prefix(article_id)}{SESSION_PREFIX}/")
        db.delete(session)
        db.flush()

    base_document = s3.get_json(version.storage_prefix)
    document = base_document if isinstance(base_document, dict) else _empty_document(article)
    document = butex_worker_client.normalize_document(document)
    document = _synchronize_document_metadata(
        document,
        title=article.title,
        abstract=article.abstract,
    )

    session = ArticleSession(
        article_id=article.id,
        article_version_id=version.id,
        revision=0,
        last_saved_revision=0,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(session)
    db.flush()
    s3.put_json_at(session_storage_prefix(article_id), SESSION_DOCUMENT, document)
    db.commit()
    db.refresh(session)
    _write_meta(article_id, session)
    return session, document


def get_session_document(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    session, document = get_or_create_session(db, article_id, actor)
    return {
        "revision": session.revision,
        "last_saved_revision": session.last_saved_revision,
        "document": document,
    }


def get_session_outline(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    session, document = get_or_create_session(db, article_id, actor)
    outline = butex_worker_client.outline_document(document)
    return {
        "revision": session.revision,
        "last_saved_revision": session.last_saved_revision,
        "outline": outline,
    }


def get_session_blocks(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    session, document = get_or_create_session(db, article_id, actor)
    blocks = document.get("blocks")
    return {
        "revision": session.revision,
        "last_saved_revision": session.last_saved_revision,
        "blocks": blocks if isinstance(blocks, list) else [],
    }


def update_article_metadata(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    payload: ArticleUpdate,
) -> Article:
    """Update authoritative metadata and an active current session as one operation."""
    _current_draft_article_and_version(db, article_id, actor)
    session = _lock_current_session(db, article_id)
    article, version = _lock_metadata_rows(db, article_id)
    if session is None:
        # A concurrent first-session creator may have committed while this
        # request waited for the Article lock.
        session = _lock_current_session(db, article_id)
    title = payload.title if "title" in payload.model_fields_set else article.title
    abstract = (
        payload.abstract
        if "abstract" in payload.model_fields_set
        else article.abstract
    )

    session_changed = False
    if session and session.article_version_id == version.id:
        current_document = _session_document(article_id)
        next_document = _synchronize_document_metadata(
            current_document,
            title=title,
            abstract=abstract,
        )
        if next_document != current_document:
            session.revision += 1
            session.updated_by = actor.user_id
            session.updated_at = datetime.now(UTC)
            s3.put_json_at(
                session_storage_prefix(article_id),
                SESSION_DOCUMENT,
                next_document,
            )
            session_changed = True

    article.title = title
    article.abstract = abstract
    article.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(article)
    if session_changed and session:
        db.refresh(session)
        _write_meta(article_id, session)
    return article


def _assert_asset_exists(
    article_id: uuid.UUID,
    version: ArticleVersion,
    asset_id: str,
) -> None:
    compile_service.validate_asset_keys([asset_id])
    try:
        s3.get_bytes(version.storage_prefix, asset_id)
    except HTTPException as exc:
        if exc.status_code == 404:
            raise HTTPException(status_code=422, detail="أصل الصورة غير موجود.") from exc
        raise


def apply_session_command(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    payload: DocumentCommandPayload,
) -> dict[str, Any]:
    article, version = _current_draft_article_and_version(db, article_id, actor)
    submitted_command = payload.command.model_dump(exclude_unset=True)
    if (
        actor.auth_method == "agent"
        and submitted_command.get("op") == "update_document_meta"
        and "authors" in submitted_command
    ):
        raise HTTPException(
            status_code=403,
            detail="لا تسمح أدوات الوكيل بتعديل مؤلفي المقال.",
        )
    metadata_update: ArticleUpdate | None = None
    if submitted_command.get("op") == "update_document_meta":
        metadata_fields = {
            field: submitted_command[field]
            for field in ("title", "abstract")
            if field in submitted_command
        }
        if metadata_fields:
            try:
                metadata_update = ArticleUpdate.model_validate(metadata_fields)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail="بيانات عنوان المقال أو ملخصه غير صالحة.",
                ) from exc
    session, current_document = get_or_create_session(db, article_id, actor)
    request_hash = _request_hash(payload)

    existing = _command_record(article_id, payload.command_id)
    if existing:
        if existing.get("request_hash") != request_hash:
            raise _COMMAND_ID_CONFLICT
        response = existing.get("response")
        if isinstance(response, dict):
            return response
        raise HTTPException(status_code=502, detail="سجل أمر الجلسة غير صالح.")

    if payload.base_revision != session.revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "revision_conflict",
                "message": "تغيّرت جلسة التحرير؛ أعد تحميلها ثم حاول مرة أخرى.",
                "current_revision": session.revision,
            },
        )

    command = _worker_command(payload, actor)
    if command.get("op") == "update_document_meta":
        command["title"] = (
            metadata_update.title
            if metadata_update and "title" in metadata_update.model_fields_set
            else article.title
        )
        command["abstract"] = (
            metadata_update.abstract
            if metadata_update and "abstract" in metadata_update.model_fields_set
            else article.abstract
        ) or ""
    if command.get("op") in {"insert_figure", "update_figure"}:
        asset_id = command.get("asset_id")
        if command.get("op") == "insert_figure" and not isinstance(asset_id, str):
            raise HTTPException(status_code=422, detail="مفتاح الصورة غير صالح.")
        if isinstance(asset_id, str):
            _assert_asset_exists(article_id, version, asset_id)

    next_document = butex_worker_client.apply_document_command(
        current_document,
        command,
    )

    locked = _lock_current_session(db, article_id)
    if not locked or locked.id != session.id or locked.revision != payload.base_revision:
        raise _CONFLICT

    existing = _command_record(article_id, payload.command_id)
    if existing:
        if existing.get("request_hash") != request_hash:
            raise _COMMAND_ID_CONFLICT
        response = existing.get("response")
        if isinstance(response, dict):
            return response
        raise HTTPException(status_code=502, detail="سجل أمر الجلسة غير صالح.")

    if command.get("op") == "update_document_meta":
        locked_article, locked_version = _lock_metadata_rows(db, article_id)
        if locked_version.id != locked.article_version_id:
            raise _CONFLICT
        locked_command = deepcopy(command)
        locked_command["title"] = (
            metadata_update.title
            if metadata_update and "title" in metadata_update.model_fields_set
            else locked_article.title
        )
        locked_command["abstract"] = (
            metadata_update.abstract
            if metadata_update and "abstract" in metadata_update.model_fields_set
            else locked_article.abstract
        ) or ""
        if locked_command != command:
            next_document = butex_worker_client.apply_document_command(
                current_document,
                locked_command,
            )
        command = locked_command
        article = locked_article

    affected_block_ids = _affected_block_ids(current_document, next_document, command)
    locked.revision += 1
    locked.updated_by = actor.user_id
    locked.updated_at = datetime.now(UTC)
    if command.get("op") == "update_document_meta":
        article.title = command["title"]
        article.abstract = command["abstract"] or None
        article.updated_at = datetime.now(UTC)
    response = {
        "ok": True,
        "revision": locked.revision,
        "last_saved_revision": locked.last_saved_revision,
        "document": next_document,
        "affected_block_ids": affected_block_ids,
    }
    record = {
        "command_id": str(payload.command_id),
        "request_hash": request_hash,
        "base_revision": payload.base_revision,
        "result_revision": locked.revision,
        "affected_block_ids": affected_block_ids,
        "response": response,
        "created_at": _now_iso(),
    }

    s3.put_json_at(session_storage_prefix(article_id), SESSION_DOCUMENT, next_document)
    _write_command_record(article_id, payload.command_id, record)
    db.commit()
    db.refresh(locked)
    _write_meta(article_id, locked)
    return response


def update_session_document(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
    base_revision: int,
    document: Any,
) -> dict[str, Any]:
    _current_draft_article_and_version(db, article_id, actor)
    session, _ = get_or_create_session(db, article_id, actor)
    if base_revision != session.revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "revision_conflict",
                "message": "تغيّرت جلسة التحرير؛ أعد تحميلها ثم حاول مرة أخرى.",
                "current_revision": session.revision,
            },
        )
    if not isinstance(document, dict):
        raise HTTPException(status_code=422, detail="مستند الجلسة غير صالح.")

    normalized = butex_worker_client.normalize_document(document)
    locked = _lock_current_session(db, article_id)
    if not locked or locked.id != session.id or locked.revision != base_revision:
        raise _CONFLICT

    locked.revision += 1
    locked.updated_by = actor.user_id
    locked.updated_at = datetime.now(UTC)
    s3.put_json_at(session_storage_prefix(article_id), SESSION_DOCUMENT, normalized)
    db.commit()
    db.refresh(locked)
    _write_meta(article_id, locked)
    return {
        "revision": locked.revision,
        "last_saved_revision": locked.last_saved_revision,
        "document": normalized,
    }


def save_session_to_draft(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    article, version = _current_draft_article_and_version(db, article_id, actor)
    session, document = get_or_create_session(db, article_id, actor)

    locked = _lock_current_session(db, article_id)
    if not locked or locked.id != session.id or locked.revision != session.revision:
        raise _CONFLICT

    s3.put_json(version.storage_prefix, document)
    document_hash = compile_service.hash_document(document)
    if version.compiled_document_hash != document_hash:
        version.compile_status = CompileStatus.PENDING
        version.active_compile_id = None
        version.compiled_document_hash = None

    locked.last_saved_revision = locked.revision
    locked.updated_by = actor.user_id
    locked.updated_at = datetime.now(UTC)
    article.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(locked)
    _write_meta(article_id, locked)

    return {
        "ok": True,
        "revision": locked.revision,
        "last_saved_revision": locked.last_saved_revision,
    }


def discard_session(db: Session, article_id: uuid.UUID, actor: Actor) -> None:
    article_service.assert_is_author(db, article_id, actor.user_id)
    session = _select_current_session(db, article_id)
    s3.delete_prefix(f"{session_storage_prefix(article_id)}{SESSION_PREFIX}/")
    if session:
        db.delete(session)
        db.commit()
