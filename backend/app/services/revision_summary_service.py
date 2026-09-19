"""Lazy, cached human-readable summaries for immutable draft revisions."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import ArticleDraftRevision
from app.models.revision_summary import DraftRevisionChangeSummary
from app.schemas.revision_summary import RevisionChangeSummaryV1
from app.services import article_draft_service, butex_worker_client, openrouter_client

logger = logging.getLogger(__name__)

_SUMMARY_VERSION = 1


def _validated_cached_summary(
    row: DraftRevisionChangeSummary | None,
) -> dict[str, Any] | None:
    if row is None or row.schema_version != _SUMMARY_VERSION:
        return None
    try:
        return RevisionChangeSummaryV1.model_validate(row.summary).model_dump(mode="json")
    except (ValidationError, TypeError, ValueError):
        logger.warning("Ignoring invalid cached revision change summary")
        return None


def _store_summary(
    db: Session,
    revision_id: uuid.UUID,
    summary: dict[str, Any],
) -> dict[str, Any]:
    validated = RevisionChangeSummaryV1.model_validate(summary).model_dump(mode="json")
    row = db.get(DraftRevisionChangeSummary, revision_id)
    if row is None:
        row = DraftRevisionChangeSummary(
            revision_id=revision_id,
            schema_version=_SUMMARY_VERSION,
            summary=validated,
        )
        db.add(row)
    else:
        row.schema_version = _SUMMARY_VERSION
        row.summary = validated

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        cached = _validated_cached_summary(
            db.get(DraftRevisionChangeSummary, revision_id)
        )
        if cached is not None:
            return cached
        raise
    return validated


def get_revision_change_summary(
    db: Session,
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    actor: Actor,
) -> dict[str, Any]:
    article_draft_service.assert_author(db, article_id, actor)
    revision = db.scalar(
        select(ArticleDraftRevision).where(
            ArticleDraftRevision.id == revision_id,
            ArticleDraftRevision.article_id == article_id,
        )
    )
    if revision is None:
        raise HTTPException(status_code=404, detail="المراجعة غير موجودة.")

    cached = _validated_cached_summary(
        db.get(DraftRevisionChangeSummary, revision.id)
    )
    if cached is not None:
        return {"summary": cached}

    if revision.revision_number <= 1:
        return {"summary": None}

    previous = db.scalar(
        select(ArticleDraftRevision).where(
            ArticleDraftRevision.article_id == article_id,
            ArticleDraftRevision.revision_number == revision.revision_number - 1,
        )
    )
    if previous is None:
        return {"summary": None}

    before = article_draft_service.read_document(previous)
    after = article_draft_service.read_document(revision)
    try:
        diff = butex_worker_client.diff_documents(before, after)
    except HTTPException as exc:
        logger.warning(
            "BuTeX revision diff unavailable for change summary (status=%s)",
            exc.status_code,
        )
        return {"summary": None}

    if diff["changed"] is False:
        empty = {"version": 1, "items": []}
        return {"summary": _store_summary(db, revision.id, empty)}

    summary = openrouter_client.summarize_revision_diff(diff)
    if summary is None:
        return {"summary": None}

    return {"summary": _store_summary(db, revision.id, summary)}
