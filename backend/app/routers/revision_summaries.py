import uuid

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.schemas.revision_summary import DraftRevisionChangeSummaryRead
from app.services import revision_summary_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get(
    "/{article_id}/draft/revisions/{revision_id}/change-summary",
    response_model=DraftRevisionChangeSummaryRead,
)
def get_revision_change_summary(
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    actor: ActorDep,
    db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:read")
    return revision_summary_service.get_revision_change_summary(
        db, article_id, revision_id, actor
    )
