"""Authenticated article-scoped unit conventions API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.models.article import Article
from app.schemas.unit_conventions import UnitConventions
from app.schemas.used_units import (
    ApplyUnitConventionsRequest,
    ApplyUnitConventionsResult,
    UsedUnitInventory,
)
from app.services import article_draft_service, unit_conventions_service, used_unit_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get("/{article_id}/unit-conventions", response_model=UnitConventions)
def get_unit_conventions(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    article = article_draft_service.assert_author(db, article_id, actor)
    return unit_conventions_service.get_unit_conventions(article)


@router.put("/{article_id}/unit-conventions", response_model=UnitConventions)
def put_unit_conventions(
    article_id: uuid.UUID, payload: UnitConventions, actor: ActorDep, db: DbDep
) -> dict:
    require_actor_scope(actor, "articles:draft:write")
    article_draft_service.assert_editable_author(db, article_id, actor)
    normalized = unit_conventions_service.validated_unit_conventions(payload.model_dump())
    # Registry discovery is remote I/O; do it before acquiring the row lock.
    unit_conventions_service.validate_registry_membership(normalized)
    # Serialize edits with Document2 creation. A concurrent conversion detects
    # conventions changed under its feet rather than saving a mismatched AST.
    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if article is None:
        raise article_draft_service._NOT_FOUND
    if article.status not in article_draft_service._EDITABLE_STATUSES:
        raise article_draft_service._FROZEN
    result = unit_conventions_service.replace_unit_conventions(article, normalized)
    db.add(article)
    db.commit()
    return result


@router.get(
    "/{article_id}/unit-conventions/used",
    response_model=UsedUnitInventory,
)
def get_used_units(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    return used_unit_service.get_inventory(db, article_id, actor)


@router.post(
    "/{article_id}/unit-conventions/apply",
    response_model=ApplyUnitConventionsResult,
)
def apply_unit_conventions(
    article_id: uuid.UUID, payload: ApplyUnitConventionsRequest,
    actor: ActorDep, db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:draft:write")
    return used_unit_service.apply_conventions(
        db, article_id, actor,
        base_revision=payload.base_revision,
        conventions=payload.unit_conventions.model_dump(exclude_none=True),
    )
