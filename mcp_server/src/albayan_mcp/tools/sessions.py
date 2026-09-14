"""Typed Document2 article-session tools backed exclusively by FastAPI."""

from __future__ import annotations

import base64
import uuid
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import BlobResourceContents, EmbeddedResource
from pydantic import BaseModel, ConfigDict, Field

from albayan_mcp.api_client import api_get_bytes, api_get_object, api_post_object
from albayan_mcp.schemas.document2 import DocumentCommand


ArticleId = Annotated[
    uuid.UUID,
    Field(description="Article UUID whose current editing session should be used."),
]
CommandId = Annotated[
    uuid.UUID,
    Field(
        description=(
            "Unique idempotency UUID for this logical mutation; never reuse it for a "
            "different payload."
        )
    ),
]
BaseRevision = Annotated[
    int,
    Field(
        strict=True,
        ge=0,
        description="Latest revision returned by a session read or successful command.",
    ),
]
McpDocumentCommand = Annotated[
    DocumentCommand,
    Field(description="One targeted Document2 operation selected by its op discriminator."),
]


class SessionResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DocumentOutlineEntryResult(SessionResultModel):
    id: str
    kind: Literal[
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "list",
        "table",
        "figure",
        "bibliography",
        "raw",
    ]
    command: str | None = None
    excerpt: str


class SessionOutlineResult(SessionResultModel):
    revision: int
    last_saved_revision: int
    outline: list[DocumentOutlineEntryResult]


class DocumentInlineTokenIdentityResult(SessionResultModel):
    id: str
    kind: Literal["text", "math", "cite", "ref"]
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class DocumentInlineIdsResult(SessionResultModel):
    field_id: str
    tokens: list[DocumentInlineTokenIdentityResult]


class DocumentFormatSpanResult(SessionResultModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None


class DocumentBlockMetadataResult(SessionResultModel):
    source: Literal["agent", "user"] | None = None


class DocumentListItemResult(SessionResultModel):
    id: str
    value: str | None = None
    formats: list[DocumentFormatSpanResult] | None = None
    inline_ids: DocumentInlineIdsResult | None = None
    math_objects: list[dict[str, Any] | None] | None = None
    blocks: list[DocumentBlockResult] | None = None


class DocumentBlockResult(SessionResultModel):
    """Stable block identity plus known editable structure; unknown BuTeX fields survive."""

    id: str
    node_type: str | None = None
    kind: str | None = None
    command: str | None = None
    value: str | None = None
    formats: list[DocumentFormatSpanResult] | None = None
    metadata: DocumentBlockMetadataResult | None = None
    asset_id: str | None = None
    math_objects: list[dict[str, Any] | None] | None = None
    options: dict[str, str] | None = None
    closing: str | None = None
    inline_ids: DocumentInlineIdsResult | None = None
    items: list[DocumentListItemResult] | None = None
    rows: list[list[str]] | None = None
    cell_formats: list[list[list[DocumentFormatSpanResult]]] | None = None
    cell_inline_ids: list[list[DocumentInlineIdsResult]] | None = None
    columns: str | None = None
    caption: str | None = None
    label: str | None = None
    caption_enabled: bool | None = None
    label_enabled: bool | None = None
    centered: bool | None = None
    blocks: list[DocumentBlockResult] | None = None


class SessionBlocksResult(SessionResultModel):
    revision: int
    last_saved_revision: int
    blocks: list[DocumentBlockResult]


class DocumentHijriDateResult(SessionResultModel):
    day: int
    month: str
    year: int


class DocumentMetaResult(SessionResultModel):
    title: str
    authors: str
    date: DocumentHijriDateResult
    abstract: str


class DocumentReferenceResult(SessionResultModel):
    key: str
    authors: str | None = None
    title: str | None = None
    year: str | None = None
    url: str | None = None
    venue: str | None = None
    field_separator: Literal[",", "،"] | None = None


class Document2DocumentResult(SessionResultModel):
    node_type: Literal["DocumentObject"] | None = None
    meta: DocumentMetaResult | None = None
    references: list[DocumentReferenceResult] | None = None
    blocks: list[DocumentBlockResult]


class SessionCommandResult(SessionResultModel):
    ok: bool = True
    revision: int
    last_saved_revision: int
    document: Document2DocumentResult
    affected_block_ids: list[str] = Field(default_factory=list)


class SessionSaveResult(SessionResultModel):
    ok: bool = True
    revision: int
    last_saved_revision: int


class SessionCompileErrorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class SessionCompileStatusResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "processing", "success", "failed"]
    compile_id: uuid.UUID | None = None
    requested_revision: int | None = Field(default=None, ge=0)
    compiled_revision: int | None = Field(default=None, ge=0)
    current_revision: int = Field(ge=0)
    last_saved_revision: int = Field(ge=0)
    pdf_ready: bool
    stale: bool
    error: SessionCompileErrorResult | None = None


def register_session_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_session_outline",
        title="Article session outline",
        description=(
            "Inspect an article editing session without loading full block content. Returns "
            "the latest revision, last saved revision, semantic outline, and stable block IDs. "
            "Use before editing when IDs or revision are not already known; never invent IDs."
        ),
    )
    async def get_session_outline(article_id: ArticleId) -> SessionOutlineResult:
        data = await api_get_object(
            f"/api/v1/articles/{article_id}/session/outline"
        )
        return SessionOutlineResult(**data)

    @server.tool(
        name="get_session_blocks",
        title="Article session blocks",
        description=(
            "Read canonical Document2 blocks and the latest revision for a precise structured "
            "edit. Use the returned block, field, token, list, item, and table identities; never "
            "guess or manufacture stable IDs."
        ),
    )
    async def get_session_blocks(article_id: ArticleId) -> SessionBlocksResult:
        data = await api_get_object(
            f"/api/v1/articles/{article_id}/session/blocks"
        )
        return SessionBlocksResult(**data)

    @server.tool(
        name="apply_session_command",
        title="Apply one Document2 session command",
        description=(
            "Apply exactly one targeted, typed Document2 command through FastAPI. First inspect "
            "the session unless the stable IDs and latest revision are already known. Pass that "
            "revision as base_revision. Use a new command_id for each logical mutation and never "
            "reuse it for another payload. On revision_conflict, re-read before retrying. FastAPI "
            "owns permissions, provenance, assets, revisions, idempotency, and session storage. "
            "Agents must use update_article_metadata for title/abstract and cannot change "
            "update_document_meta.authors."
        ),
    )
    async def apply_session_command(
        article_id: ArticleId,
        command_id: CommandId,
        base_revision: BaseRevision,
        command: McpDocumentCommand,
    ) -> SessionCommandResult:
        data = await api_post_object(
            f"/api/v1/articles/{article_id}/session/commands",
            json={
                "command_id": str(command_id),
                "base_revision": base_revision,
                "command": command.model_dump(exclude_unset=True),
            },
        )
        return SessionCommandResult(**data)

    @server.tool(
        name="save_session",
        title="Save article session to draft",
        description=(
            "Persist the current editing session to the article's current draft. Invoke only "
            "when the user explicitly asks to save or persist; editing commands alone do not "
            "authorize this step. FastAPI performs authorization and persistence."
        ),
    )
    async def save_session(article_id: ArticleId) -> SessionSaveResult:
        data = await api_post_object(
            f"/api/v1/articles/{article_id}/session/save"
        )
        return SessionSaveResult(**data)

    @server.tool(
        name="compile_session",
        title="Compile the current article session",
        description=(
            "Save the exact current editing session to the draft and start trusted PDF "
            "compilation through FastAPI. Invoke only when the user explicitly asks to "
            "compile or preview. Do not supply or generate LaTeX, asset keys, or hashes. "
            "This operation persists the session even if export validation later fails."
        ),
    )
    async def compile_session(article_id: ArticleId) -> SessionCompileStatusResult:
        data = await api_post_object(
            f"/api/v1/articles/{article_id}/session/compile"
        )
        return SessionCompileStatusResult(**data)

    @server.tool(
        name="get_compile_status",
        title="Get article session compile status",
        description=(
            "Inspect the latest session compilation. Poll while status is processing. "
            "If it fails, use the safe error to correct the article and compile again. "
            "A PDF can be requested only when pdf_ready is true and stale is false."
        ),
    )
    async def get_compile_status(article_id: ArticleId) -> SessionCompileStatusResult:
        data = await api_get_object(
            f"/api/v1/articles/{article_id}/session/compile/status"
        )
        return SessionCompileStatusResult(**data)

    @server.tool(
        name="get_article_pdf",
        title="Retrieve the current compiled article PDF",
        description=(
            "Retrieve and surface the PDF for the exact current session revision. Call "
            "get_compile_status first and use this only when pdf_ready is true. FastAPI "
            "blocks stale, failed, pending, processing, and legacy unbound previews."
        ),
    )
    async def get_article_pdf(article_id: ArticleId) -> EmbeddedResource:
        response = await api_get_bytes(
            f"/api/v1/articles/{article_id}/session/pdf"
        )
        if response.content_type != "application/pdf":
            raise RuntimeError("استجابة ملفّ المعاينة ليست PDF صالحة.")
        compile_id = response.headers.get("x-albayan-compile-id")
        revision = response.headers.get("x-albayan-session-revision")
        if not compile_id or not revision:
            raise RuntimeError("استجابة ملفّ المعاينة لا تتضمن هوية التجميع.")
        return EmbeddedResource(
            resource=BlobResourceContents(
                uri=f"albayan://articles/{article_id}/session/compiled.pdf",
                mime_type="application/pdf",
                blob=base64.b64encode(response.content).decode("ascii"),
            ),
            meta={
                "compile_id": compile_id,
                "session_revision": revision,
            },
        )
