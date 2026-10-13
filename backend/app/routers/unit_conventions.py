"""Authenticated article-scoped unit conventions API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.models.article import Article
from app.schemas.unit_conventions import UnitConventions
from app.services import article_draft_service, unit_conventions_service

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
    result = unit_conventions_service.replace_unit_conventions(article, payload.model_dump())
    db.add(article)
    db.commit()
    return result
