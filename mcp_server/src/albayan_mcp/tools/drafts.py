"""Typed immutable-draft tools backed exclusively by FastAPI."""

from __future__ import annotations

import base64
import uuid
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import BlobResourceContents, EmbeddedResource
from pydantic import BaseModel, ConfigDict, Field

from albayan_mcp.api_client import api_get_bytes, api_get_object, api_post_object
from albayan_mcp.schemas.draft_command import DocumentCommand
from albayan_mcp.tools.block_projection import project_draft_blocks_response

ArticleId = Annotated[
    uuid.UUID, Field(description="Article UUID whose authoritative draft should be used.")
]
CommandId = Annotated[
    uuid.UUID,
    Field(description="Unique idempotency UUID; never reuse it for a different command."),
]
BaseRevision = Annotated[
    int,
    Field(
        strict=True,
        ge=1,
        description="Latest draft revision_number returned by a read or mutation.",
    ),
]
McpDocumentCommand = Annotated[
    DocumentCommand,
    Field(
        description=(
            "One targeted Document2 operation selected by its op discriminator. "
            "For math insert/replace, call get_math_authoring_capabilities first, restrict "
            "generated canonical LaTeX to round_trip_safe, then prefer "
            "{kind:'math', latex, display, label}; do not construct recursive MathObject JSON."
        )
    ),
]


class DraftResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DocumentOutlineEntryResult(DraftResultModel):
    id: str
    kind: Literal[
        "section", "subsection", "subsubsection", "paragraph", "list",
        "table", "figure", "bibliography", "raw",
    ]
    command: str | None = None
    excerpt: str


class DraftOutlineResult(DraftResultModel):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    outline: list[DocumentOutlineEntryResult]


class DraftBlocksResult(DraftResultModel):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    blocks: list[dict[str, Any]]


class DocumentReferenceResult(DraftResultModel):
    key: str
    authors: str
    title: str
    year: str
    venue: str
    url: str
    field_separator: Literal[",", "،"]


class DraftReferencesResult(DraftResultModel):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    references: list[DocumentReferenceResult]


class DocumentCitationIndexEntryResult(DraftResultModel):
    kind: Literal["cite"]
    block_id: str
    field_id: str
    token_id: str
    keys: list[str]
    unresolved_keys: list[str]


class DocumentCrossReferenceIndexEntryResult(DraftResultModel):
    kind: Literal["ref"]
    ref_command: Literal["ref", "eqref"]
    block_id: str
    field_id: str
    token_id: str
    keys: list[str]
    unresolved_keys: list[str]


class DocumentIndexedLabelResult(DraftResultModel):
    key: str
    kind: Literal["fig", "tab", "eq"]
    caption: str
    number: int
    block_id: str | None = None
    field_id: str | None = None
    token_id: str | None = None


class DocumentUnresolvedReferencesResult(DraftResultModel):
    citation_keys: list[str]
    cross_reference_keys: list[str]


class DocumentReferenceIndexResult(DraftResultModel):
    citations: list[DocumentCitationIndexEntryResult]
    cross_references: list[DocumentCrossReferenceIndexEntryResult]
    labels: list[DocumentIndexedLabelResult]
    unresolved: DocumentUnresolvedReferencesResult


class DraftReferenceIndexResult(DraftResultModel):
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    reference_index: DocumentReferenceIndexResult


class DraftDocumentResult(DraftResultModel):
    node_type: str | None = None
    meta: dict[str, Any] | None = None
    references: list[dict[str, Any]] | None = None
    blocks: list[dict[str, Any]]


class DraftCommandResult(DraftResultModel):
    ok: bool = True
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    document_hash: str
    actor_type: Literal["human", "agent", "system"]
    reason: Literal["initial", "autosave", "ai_edit", "metadata_edit", "restore"]
    document: DraftDocumentResult
    affected_block_ids: list[str] = Field(default_factory=list)


class DraftCompileErrorResult(BaseModel):
    code: str
    message: str


class DraftCompileStatusResult(BaseModel):
    status: Literal["pending", "processing", "success", "failed"]
    compile_id: uuid.UUID | None = None
    revision_id: uuid.UUID
    revision_number: int = Field(ge=1)
    pdf_ready: bool
    error: DraftCompileErrorResult | None = None


def register_draft_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_draft_outline",
        title="Article draft outline",
        description=(
            "Inspect the authoritative draft outline and stable block IDs. Use the returned "
            "revision_number as base_revision; never invent IDs."
        ),
    )
    async def get_draft_outline(article_id: ArticleId) -> DraftOutlineResult:
        return DraftOutlineResult(
            **await api_get_object(f"/api/v1/articles/{article_id}/draft/outline")
        )

    @server.tool(
        name="get_draft_blocks",
        title="Article draft blocks",
        description=(
            "Read compact Document2 prose/structure plus stable block, field, token, list, and "
            "table identities for precise edits. Recursive equation MathObject payloads are "
            "omitted; use get_draft_equations for equation details. Never manufacture IDs."
        ),
    )
    async def get_draft_blocks(article_id: ArticleId) -> DraftBlocksResult:
        data = await api_get_object(f"/api/v1/articles/{article_id}/draft/blocks")
        return DraftBlocksResult(**project_draft_blocks_response(data))

    @server.tool(
        name="get_draft_references",
        title="Article draft bibliography references",
        description=(
            "Read the current canonical Document2 bibliography catalog through FastAPI. "
            "This is a pure read: it needs no command_id or base_revision and creates no revision."
        ),
    )
    async def get_draft_references(article_id: ArticleId) -> DraftReferencesResult:
        return DraftReferencesResult(
            **await api_get_object(f"/api/v1/articles/{article_id}/draft/references")
        )

    @server.tool(
        name="get_draft_reference_index",
        title="Article draft citation and cross-reference index",
        description=(
            "Read BuTeX's semantic index of cite/ref/eqref tokens, labels, stable IDs, and "
            "unresolved keys for the current canonical draft. This is a pure read and does "
            "not rebuild the index in MCP or mutate the draft."
        ),
    )
    async def get_draft_reference_index(
        article_id: ArticleId,
    ) -> DraftReferenceIndexResult:
        return DraftReferenceIndexResult(
            **await api_get_object(
                f"/api/v1/articles/{article_id}/draft/reference-index"
            )
        )

    @server.tool(
        name="apply_draft_command",
        title="Apply one draft command",
        description=(
            "Create an immutable draft revision with one typed Document2 command. Pass the "
            "latest revision_number and a fresh command_id. Before generating new math, call "
            "get_math_authoring_capabilities and restrict canonical LaTeX to round_trip_safe. "
            "For math insert/replace, send that ordinary canonical LaTeX in the compact math "
            "token; FastAPI/Burhan builds the structured equation. Re-read on revision_conflict. "
            "FastAPI owns authorization, normalization, assets, metadata sync, provenance, "
            "idempotency, and persistence. Agent edits remain visible in draft history. Agents "
            "cannot change authors or restore historical revisions; restore is human-only."
        ),
    )
    async def apply_draft_command(
        article_id: ArticleId,
        command_id: CommandId,
        base_revision: BaseRevision,
        command: McpDocumentCommand,
    ) -> DraftCommandResult:
        data = await api_post_object(
            f"/api/v1/articles/{article_id}/draft/commands",
            json={
                "command_id": str(command_id),
                "base_revision": base_revision,
                "command": command.model_dump(exclude_unset=True),
            },
        )
        return DraftCommandResult(**data)

    @server.tool(
        name="compile_draft",
        title="Compile the current draft",
        description=(
            "Start trusted server-side compilation of the exact current immutable revision. "
            "Invoke only when the user asks to compile or preview; never supply LaTeX or hashes."
        ),
    )
    async def compile_draft(article_id: ArticleId) -> DraftCompileStatusResult:
        return DraftCompileStatusResult(
            **await api_post_object(f"/api/v1/articles/{article_id}/draft/compile")
        )

    @server.tool(
        name="get_compile_status",
        title="Get draft compile status",
        description="Check the compile attempt bound to the exact current draft revision.",
    )
    async def get_compile_status(article_id: ArticleId) -> DraftCompileStatusResult:
        return DraftCompileStatusResult(
            **await api_get_object(f"/api/v1/articles/{article_id}/draft/compile/status")
        )

    @server.tool(
        name="get_article_pdf",
        title="Retrieve the current draft PDF",
        description="Retrieve the PDF only when get_compile_status reports pdf_ready=true.",
    )
    async def get_article_pdf(article_id: ArticleId) -> EmbeddedResource:
        response = await api_get_bytes(f"/api/v1/articles/{article_id}/draft/pdf")
        if response.content_type != "application/pdf":
            raise RuntimeError("استجابة ملفّ المعاينة ليست PDF صالحة.")
        compile_id = response.headers.get("x-albayan-compile-id")
        revision = response.headers.get("x-albayan-draft-revision")
        if not compile_id or not revision:
            raise RuntimeError("استجابة ملفّ المعاينة لا تتضمن هوية التجميع.")
        return EmbeddedResource(
            resource=BlobResourceContents(
                uri=f"albayan://articles/{article_id}/draft/compiled.pdf",
                mime_type="application/pdf",
                blob=base64.b64encode(response.content).decode("ascii"),
            ),
            meta={"compile_id": compile_id, "draft_revision": revision},
        )
