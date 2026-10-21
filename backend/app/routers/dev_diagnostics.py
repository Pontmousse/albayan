from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.core.actor import ActorDep
from app.core.config import settings
from app.schemas.dev_diagnostics import DocumentDiagnosticRequest, EquationDiagnosticRequest
from app.services import document_diagnostic_service, equation_diagnostic_service

router = APIRouter(prefix="/api/v1/dev/diagnostics", tags=["dev-diagnostics"])


@router.post("/document")
def inspect_document(
    payload: DocumentDiagnosticRequest,
    actor: ActorDep,
) -> dict:
    del actor
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")
    if len(json.dumps(payload.payload, ensure_ascii=False).encode("utf-8")) > 131_072:
        raise HTTPException(status_code=413, detail="Diagnostic fixture too large")
    return document_diagnostic_service.inspect_document(
        operation=payload.operation, payload=payload.payload
    )


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
        unit_conventions=payload.unit_conventions.model_dump(),
    )
