from __future__ import annotations

from fastapi import APIRouter

from app.core.actor import ActorDep, require_actor_scope
from app.schemas.math_authoring import MathAuthoringCapabilitiesRead
from app.services.math_authoring_capabilities import get_math_authoring_capabilities
from app.services.unit_conventions_service import get_unit_registry

router = APIRouter(prefix="/api/v1/math", tags=["math"])


@router.get(
    "/authoring-capabilities",
    response_model=MathAuthoringCapabilitiesRead,
)
def read_math_authoring_capabilities(actor: ActorDep) -> dict:
    """Return the deterministic canonical-LaTeX authoring contract without mutation."""

    require_actor_scope(actor, "articles:read")
    return get_math_authoring_capabilities()


@router.get("/unit-registry")
def read_unit_registry(actor: ActorDep) -> dict:
    """Expose Burhan's authoritative unit catalogue to authenticated AI authors.

    No local registry replica or unauthenticated Burhan bypass. Upstream
    unavailability is surfaced rather than substituting a guessed catalogue.
    """
    require_actor_scope(actor, "articles:read")
    return get_unit_registry()
