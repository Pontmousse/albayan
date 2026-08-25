from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from albayan_mcp import server as server_module
from albayan_mcp.tools.articles import ArticleSummaryResult, register_article_tools
from tests.test_profile_tools import FakeServer


class ArticleToolTests(unittest.IsolatedAsyncioTestCase):
    def test_direct_registration_exposes_read_articles(self) -> None:
        fake_server = FakeServer()

        register_article_tools(fake_server)

        self.assertIn("read_articles", fake_server.tools)

    def test_create_server_exposes_profile_and_articles_tools(self) -> None:
        with patch(
            "albayan_mcp.server.MCPServer",
            FakeServer,
        ), patch.object(
            server_module,
            "settings",
            SimpleNamespace(oauth_enabled=False),
        ):
            mcp = server_module.create_server()

        self.assertIn("get_my_profile", mcp.tools)
        self.assertIn("read_articles", mcp.tools)

    async def test_read_articles_calls_backend_and_returns_structured_output(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)
        article = {
            "id": "article-1",
            "title": "عنوان المقال",
            "status": "draft",
            "version_number": 2,
            "updated_at": "2026-01-01T12:00:00Z",
            "submitted_at": None,
        }

        with patch(
            "albayan_mcp.tools.articles.api_get_list",
            new=AsyncMock(return_value=[article]),
        ) as api_get_list:
            result = await fake_server.tools["read_articles"]()

        api_get_list.assert_awaited_once_with("/api/v1/articles/me")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ArticleSummaryResult)
        self.assertEqual(result[0].model_dump(), article)

    async def test_read_articles_handles_zero_articles(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)

        with patch(
            "albayan_mcp.tools.articles.api_get_list",
            new=AsyncMock(return_value=[]),
        ):
            result = await fake_server.tools["read_articles"]()

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
