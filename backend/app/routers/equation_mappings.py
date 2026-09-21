import uuid

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.core.clerk import DbDep
from app.schemas.equation_mapping import EquationMappingsRead, EquationMappingsUpdate
from app.services import article_draft_service, equation_mapping_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get(
    "/{article_id}/equation-mappings",
    response_model=EquationMappingsRead,
)
def get_equation_mappings(
    article_id: uuid.UUID,
    actor: ActorDep,
    db: DbDep,
) -> dict[str, dict[str, str]]:
    require_actor_scope(actor, "articles:read")
    article = article_draft_service.assert_editable_author(db, article_id, actor)
    return {"mappings": equation_mapping_service.get_equation_mappings(article)}


@router.put(
    "/{article_id}/equation-mappings",
    response_model=EquationMappingsRead,
)
def put_equation_mappings(
    article_id: uuid.UUID,
    payload: EquationMappingsUpdate,
    actor: ActorDep,
    db: DbDep,
) -> dict[str, dict[str, str]]:
    require_actor_scope(actor, "articles:draft:write")
    article = article_draft_service.assert_editable_author(db, article_id, actor)
    mappings = equation_mapping_service.replace_equation_mappings(
        article,
        payload.mappings,
    )
    db.add(article)
    db.commit()
    return {"mappings": mappings}
