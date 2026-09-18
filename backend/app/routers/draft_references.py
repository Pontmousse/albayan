"""Read-only draft reference introspection routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.schemas.article import DraftReferenceIndexRead, DraftReferencesRead
from app.services import draft_reference_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get("/{article_id}/draft/references", response_model=DraftReferencesRead)
def get_draft_references(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    return draft_reference_service.get_references(db, article_id, actor)


@router.get(
    "/{article_id}/draft/reference-index",
    response_model=DraftReferenceIndexRead,
)
def get_draft_reference_index(
    article_id: uuid.UUID, actor: ActorDep, db: DbDep
) -> dict:
    require_actor_scope(actor, "articles:read")
    return draft_reference_service.get_reference_index(db, article_id, actor)
