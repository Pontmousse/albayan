from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from albayan_mcp.api_client import api_get_list


class ArticleSummaryResult(BaseModel):
    id: str
    title: str
    status: str
    version_number: int
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
