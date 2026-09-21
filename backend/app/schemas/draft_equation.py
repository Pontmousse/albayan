from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DraftEquationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str
    field_id: str
    token_id: str
    container: Literal[
        "paragraph",
        "heading",
        "list_item",
        "table_cell",
        "table_caption",
        "figure_caption",
    ]
    latex: str | None
    display: bool
    label: str | None = None
    editable: bool
    warnings: list[str] | None = None


class DraftEquationsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: UUID
    revision_number: int
    document_language: Literal["ar"]
    equation_representation: Literal["canonical_english_latex"]
    variable_mappings: dict[str, str]
    equations: list[DraftEquationRead]
