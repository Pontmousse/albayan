from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.actor import ActorDep
from app.core.config import settings
from app.schemas.dev_diagnostics import EquationDiagnosticRequest
from app.services import equation_diagnostic_service

router = APIRouter(prefix="/api/v1/dev/diagnostics", tags=["dev-diagnostics"])


@router.post("/equation")
def inspect_equation(
    payload: EquationDiagnosticRequest,
    actor: ActorDep,
) -> dict:
    # Requiring ActorDep keeps this behind normal human/agent authentication;
    # the explicit DEV_MODE gate prevents this diagnostic surface from being
    # enabled accidentally in production. No user/article state is read.
    del actor
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")
    return equation_diagnostic_service.inspect_equation(
        latex=payload.latex,
        display=payload.display,
        model_tier=payload.model_tier,
    )
