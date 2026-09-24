from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EquationDiagnosticRequest(BaseModel):
    latex: str = Field(min_length=1, max_length=10_000)
    display: bool = False
    model_tier: Literal["heuristic", "cheap", "medium"] = "heuristic"
