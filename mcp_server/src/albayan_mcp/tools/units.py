"""Normal user-facing MCP tools for canonical article unit notation.

These tools use only Al-Bayan FastAPI. The global catalogue is always fetched
from Burhan through FastAPI; there is no second registry in the MCP layer.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from albayan_mcp.api_client import api_get_object, api_post_object
from albayan_mcp.tools.drafts import DraftDocumentResult


ArticleId = Annotated[
    uuid.UUID,
    Field(description="Article UUID for the authenticated author's current draft."),
]
BaseRevision = Annotated[
    int,
    Field(ge=1, strict=True,
          description="Latest revision_number from get_article_unit_context or get_draft_outline."),
]


class UnitResult(BaseModel):
    model_config = ConfigDict(extra="allow")


class UnitRegistryResult(UnitResult):
    version: int
    canonical_syntax: str
    token_pattern: str
    notation_only: Literal[True]
    units: dict[str, dict[str, Any]]


class CustomUnitDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    display: Annotated[str, Field(min_length=1, max_length=64)]
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None


class UnitConventionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    overrides: dict[str, str] = Field(default_factory=dict)
    custom_units: dict[str, CustomUnitDefinition] = Field(default_factory=dict)


class UsedUnitResult(UnitResult):
    token: str
    usage_count: int = Field(ge=1)
    status: Literal["registry", "custom", "unknown"]
    display: str
    source: Literal["registry_default", "article_override", "article_custom", "unknown"]
    name: str | None = None
    name_ar: str | None = None
    default_display: str | None = None
    alternatives: list[str] = Field(default_factory=list)


class ArticleUnitContextResult(UnitResult):
    revision_number: int = Field(ge=1)
    unit_conventions: UnitConventionsInput
    used_units: list[UsedUnitResult]
    registered_tokens: list[str] = Field(default_factory=list)


class AppliedUnitConventionsResult(UnitResult):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    document_hash: str
    actor_type: Literal["human", "agent", "system"]
    reason: Literal["unit_conventions", "initial", "autosave", "ai_edit", "metadata_edit", "restore", "revision_request"]
    unit_conventions: UnitConventionsInput
    document: DraftDocumentResult
    affected_block_ids: list[str] = Field(default_factory=list)
    used_units: list[UsedUnitResult] = Field(default_factory=list)


def register_unit_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_unit_registry",
        title="Burhan canonical unit registry and notation rules",
        description=(
            "Pure read. Discover the live Burhan-owned global registry via Al-Bayan FastAPI: "
            "canonical \\mathsf{token} syntax, case-sensitive token grammar "
            "^[A-Za-z][A-Za-z0-9]*$, Arabic defaults, alternatives, names, and "
            "notation_only=true. There is NO registry copy in MCP. "
            "Each \\mathsf{...} is an explicit unit atom; scripts and operators remain "
            "outside it (30\\mathsf{m}/\\mathsf{s}, 2\\mathsf{m}^2). "
            "Bare N is a variable; \\mathsf{N} is a unit and \\mathbb{N} a number set. "
            "Unknown explicit tokens are preserved with a warning, never guessed. "
            "No numerical conversion or dimensional analysis. "
            "For an article's custom units/overrides, call get_article_unit_context."
        ),
    )
    async def get_unit_registry() -> UnitRegistryResult:
        return UnitRegistryResult(
            **await api_get_object("/api/v1/math/unit-registry")
        )

    @server.tool(
        name="get_article_unit_context",
        title="Current article unit conventions and used units",
        description=(
            "Pure article-scoped read. Returns the current article's complete "
            "unit_conventions (registered overrides plus article-only custom units) "
            "and the used-unit inventory with counts, display source and unknown status. "
            "Use with get_unit_registry BEFORE AI writes canonical math. "
            "Preserve the exact case-sensitive custom canonical token; "
            "author \\mathsf{CU}, not the Arabic display. Do not treat bare variables "
            "as units. Unknown tokens remain explicit and must not be guessed. "
            "Take revision_number from this read for subsequent apply operations. "
            "Never conflate unit_conventions with variable_mappings."
        ),
    )
    async def get_article_unit_context(
        article_id: ArticleId,
    ) -> ArticleUnitContextResult:
        return ArticleUnitContextResult(
            **await api_get_object(
                f"/api/v1/articles/{article_id}/unit-conventions/used"
            )
        )

    @server.tool(
        name="apply_article_unit_conventions",
        title="Apply notation-only unit conventions to the current draft",
        description=(
            "Apply the FULL new unit_conventions state, not a partial patch. "
            "First call get_article_unit_context and preserve all unrelated existing "
            "overrides/custom_units. Base revision must be current; on 409 re-read "
            "and do not blindly retry. Registered overrides may change display only, "
            "not canonical meaning. Custom units require a case-sensitive canonical "
            "identifier plus display, and optional human-readable name; never shadow "
            "a registered token or delete a custom token used in equations. "
            "Safe displays contain Unicode letters/marks/digits, single spaces or "
            "period/middle-dot/hyphen/Arabic decimal separator, max 64 characters; "
            "not arbitrary LaTeX. FastAPI validates against Burhan's live registry. "
            "Updates only affected Document2 unit atoms and creates a new immutable "
            "revision; older revisions are unchanged. No numeric conversion. "
            "For new equations, use canonical \\mathsf{token} with apply_draft_command."
        ),
    )
    async def apply_article_unit_conventions(
        article_id: ArticleId,
        base_revision: BaseRevision,
        unit_conventions: UnitConventionsInput,
    ) -> AppliedUnitConventionsResult:
        return AppliedUnitConventionsResult(
            **await api_post_object(
                f"/api/v1/articles/{article_id}/unit-conventions/apply",
                json={
                    "base_revision": base_revision,
                    "unit_conventions": unit_conventions.model_dump(exclude_none=True),
                },
            )
        )
