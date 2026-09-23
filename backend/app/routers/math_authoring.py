from __future__ import annotations

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.schemas.math_authoring import MathAuthoringCapabilitiesRead
from app.services.math_authoring_capabilities import get_math_authoring_capabilities

router = APIRouter(prefix="/api/v1/math", tags=["math"])


@router.get(
    "/authoring-capabilities",
    response_model=MathAuthoringCapabilitiesRead,
)
def read_math_authoring_capabilities(actor: ActorDep) -> dict:
    """Return the deterministic canonical-LaTeX authoring contract without mutation."""

    require_actor_scope(actor, "articles:read")
    return get_math_authoring_capabilities()
