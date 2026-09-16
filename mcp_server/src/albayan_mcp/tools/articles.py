from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field

from albayan_mcp.api_client import (
    api_get_list,
    api_get_object,
    api_patch_object,
    api_post_object,
)


ArticleId = Annotated[
    uuid.UUID,
    Field(description="Article UUID returned by create_article or read_articles."),
]
ArticleTitle = Annotated[
    str,
    Field(
        min_length=1,
        max_length=500,
        description="Draft article title; surrounding whitespace is removed by FastAPI.",
    ),
]
ArticleAbstract = Annotated[
    str,
    Field(
        max_length=5000,
        description="Optional draft abstract. Use an empty string to clear it during update.",
    ),
]


class ArticleResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ArticleVersionResult(ArticleResultModel):
    id: uuid.UUID
    version_number: int
    source_type: str
    source_draft_revision_id: uuid.UUID | None = None
    document_hash: str
    title_snapshot: str
    abstract_snapshot: str | None = None
    submitted_at: datetime | None = None
    created_at: datetime


class ArticleDetailResult(ArticleResultModel):
    id: uuid.UUID
    title: str
    abstract: str | None
    status: str
    current_draft_revision_id: uuid.UUID | None
    draft_revision_number: int
    created_at: datetime
    updated_at: datetime
    latest_version: ArticleVersionResult | None
    versions: list[ArticleVersionResult]


class ArticleSummaryResult(BaseModel):
    id: str
    title: str
    status: str
    latest_version_number: int | None
    updated_at: str
    submitted_at: str | None


def register_article_tools(server: MCPServer) -> None:
    @server.tool(
        name="read_articles",
        title="مقالاتي",
        description="قراءة قائمة مقالات المستخدم الحالي من مجلة البيان.",
    )
    async def read_articles() -> list[ArticleSummaryResult]:
        articles = await api_get_list("/api/v1/articles/me")
        return [ArticleSummaryResult(**article) for article in articles]

    @server.tool(
        name="create_article",
        title="Create a draft article",
        description=(
            "Create a new draft article owned by the authenticated user. FastAPI adds that "
            "user as the corresponding ArticleAuthor. This tool cannot submit the article or "
            "add, remove, or reorder authors."
        ),
    )
    async def create_article(
        title: ArticleTitle,
        abstract: ArticleAbstract = None,
    ) -> ArticleDetailResult:
        payload = {"title": title}
        if abstract is not None:
            payload["abstract"] = abstract
        article = await api_post_object("/api/v1/articles", json=payload)
        return ArticleDetailResult(**article)

    @server.tool(
        name="get_article",
        title="Get draft article details",
        description=(
            "Read typed article and version metadata for an article owned by the authenticated "
            "user. Use the Document2 draft inspection tools for block contents and stable IDs."
        ),
    )
    async def get_article(article_id: ArticleId) -> ArticleDetailResult:
        article = await api_get_object(f"/api/v1/articles/{article_id}")
        return ArticleDetailResult(**article)

    @server.tool(
        name="update_article_metadata",
        title="Update draft article metadata",
        description=(
            "Update the title and/or abstract of an owned draft. Provide at least one field; an "
            "empty abstract clears it. FastAPI synchronizes the authoritative Article row and "
            "the canonical Document2 draft as a new immutable revision. Re-inspect the draft "
            "before the next structured edit. This tool cannot edit authors or submit an article."
        ),
    )
    async def update_article_metadata(
        article_id: ArticleId,
        base_revision: Annotated[
            int,
            Field(ge=1, strict=True, description="Current draft revision_number."),
        ],
        title: ArticleTitle = None,
        abstract: ArticleAbstract = None,
    ) -> ArticleDetailResult:
        payload: dict[str, str | int] = {"base_revision": base_revision}
        if title is not None:
            payload["title"] = title
        if abstract is not None:
            payload["abstract"] = abstract
        if len(payload) == 1:
            raise ToolError(
                "يجب إرسال title أو abstract على الأقل؛ استخدم نصاً فارغاً لمسح الملخص."
            )
        article = await api_patch_object(
            f"/api/v1/articles/{article_id}",
            json=payload,
        )
        return ArticleDetailResult(**article)
