"""Compact equation reads for the current authoritative draft."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from albayan_mcp.api_client import api_get_object

ArticleId = Annotated[
    uuid.UUID, Field(description="Article UUID whose authoritative draft equations should be read.")
]


class EquationResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DraftEquationResult(EquationResultModel):
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


class DraftEquationsResult(EquationResultModel):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    document_language: Literal["ar"]
    equation_representation: Literal["canonical_english_latex"]
    variable_mappings: dict[str, str]
    equations: list[DraftEquationResult]


def register_equation_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_draft_equations",
        title="Article draft equations",
        description=(
            "Read a compact inventory of equations from the current authoritative Arabic "
            "article draft. Returned LaTeX is canonical English interoperability notation for "
            "the AI, not the journal's user-facing mathematical language. The response includes "
            "the current Latin-to-Arabic variable mappings once at top level and exact block, "
            "field, and token IDs for later inline-token edits. This is a pure read and does not "
            "compile, mutate the draft, or persist reverse mappings."
        ),
    )
    async def get_draft_equations(article_id: ArticleId) -> DraftEquationsResult:
        return DraftEquationsResult(
            **await api_get_object(f"/api/v1/articles/{article_id}/draft/equations")
        )
