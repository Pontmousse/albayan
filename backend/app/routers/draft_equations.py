import uuid

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.schemas.draft_equation import DraftEquationsRead
from app.services import draft_equation_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get(
    "/{article_id}/draft/equations",
    response_model=DraftEquationsRead,
    response_model_exclude_none=True,
)
def get_draft_equations(
    article_id: uuid.UUID,
    actor: ActorDep,
    db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:read")
    return draft_equation_service.get_equations(db, article_id, actor)
