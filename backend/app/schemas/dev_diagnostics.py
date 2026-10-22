from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.unit_conventions import UnitConventions


class DocumentDiagnosticRequest(BaseModel):
    operation: Literal[
        "diagnose_contract", "normalize", "outline", "references",
        "reference_index", "export", "diff", "apply_command",
        "diagnose_math_object", "project_math_object_english",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


class EquationDiagnosticRequest(BaseModel):
    latex: str = Field(min_length=1, max_length=10_000)
    display: bool = False
    model_tier: Literal["heuristic", "cheap", "medium"] = "heuristic"
    unit_conventions: UnitConventions = Field(default_factory=UnitConventions)
