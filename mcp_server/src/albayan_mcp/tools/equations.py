"""Compact equation reads and canonical math-authoring capability discovery."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

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


class MathAuthoringCapabilitiesResult(EquationResultModel):
    contract_version: Literal[1]
    canonical_input: Literal[True]
    representation: Literal["canonical_english_latex"]
    instruction: str
    preferred_submission: dict[str, Any]
    source_snapshot: dict[str, Any]
    round_trip_safe: dict[str, Any]
    accepted_but_not_round_trip_safe: dict[str, Any]
    unsupported_or_forbidden: dict[str, Any]
    normalization_aliases: list[dict[str, str]]
    constraints: list[str]
    examples: list[dict[str, Any]]


def register_equation_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_math_authoring_capabilities",
        title="Canonical equation LaTeX authoring capabilities",
        description=(
            "Call this pure-read tool before generating new equation LaTeX. It returns the "
            "canonical ordinary English-LaTeX whitelist that the current Albayan -> Burhan -> "
            "Document2 path can author safely, plus syntax that Burhan can parse/build but that "
            "is not reliable for editor round-trip. Restrict newly generated math to "
            "round_trip_safe. Never emit Arabic-side/internal Burhan or BuTeX macros such as "
            "\\ad, \\arsum, \\arprod, \\arlim, \\boldarabic, or \\butextakween. This tool "
            "does not read or mutate an article and needs no article ID."
        ),
    )
    async def get_math_authoring_capabilities() -> MathAuthoringCapabilitiesResult:
        return MathAuthoringCapabilitiesResult(
            **await api_get_object("/api/v1/math/authoring-capabilities")
        )

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
