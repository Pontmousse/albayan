from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from albayan_mcp import server as server_module
from albayan_mcp.tools.articles import (
    ArticleDetailResult,
    ArticleSummaryResult,
    register_article_tools,
)
from tests.test_profile_tools import FakeServer


class ArticleToolTests(unittest.IsolatedAsyncioTestCase):
    def test_direct_registration_exposes_article_tools(self) -> None:
        fake_server = FakeServer()

        register_article_tools(fake_server)

        self.assertEqual(
            set(fake_server.tools),
            {
                "read_articles",
                "create_article",
                "get_article",
                "update_article_metadata",
            },
        )

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

        self.assertEqual(
            set(mcp.tools),
            {
                "get_my_profile",
                "read_articles",
                "create_article",
                "get_article",
                "update_article_metadata",
                "get_draft_outline",
                "get_draft_blocks",
                "apply_draft_command",
                "compile_draft",
                "get_compile_status",
                "get_article_pdf",
                "list_article_assets",
                "get_article_asset",
                "upload_article_asset",
            },
        )

    async def test_read_articles_calls_backend_and_returns_structured_output(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)
        article = {
            "id": "article-1",
            "title": "عنوان المقال",
            "status": "draft",
            "latest_version_number": None,
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

    def _article_detail(self, article_id: str) -> dict:
        version = {
            "id": "22222222-2222-2222-2222-222222222222",
            "version_number": 1,
            "source_type": "web_editor",
            "source_draft_revision_id": "33333333-3333-3333-3333-333333333333",
            "document_hash": "a" * 64,
            "title_snapshot": "عنوان",
            "abstract_snapshot": "ملخص",
            "submitted_at": None,
            "created_at": "2026-09-13T12:00:00Z",
        }
        return {
            "id": article_id,
            "title": "عنوان",
            "abstract": "ملخص",
            "status": "submitted",
            "current_draft_revision_id": "33333333-3333-3333-3333-333333333333",
            "draft_revision_number": 2,
            "created_at": "2026-09-13T12:00:00Z",
            "updated_at": "2026-09-13T12:00:00Z",
            "latest_version": version,
            "versions": [version],
        }

    async def test_create_article_posts_only_title_and_supplied_abstract(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)
        response = self._article_detail("11111111-1111-1111-1111-111111111111")

        with patch(
            "albayan_mcp.tools.articles.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            result = await fake_server.tools["create_article"]("عنوان", "ملخص")

        post.assert_awaited_once_with(
            "/api/v1/articles",
            json={"title": "عنوان", "abstract": "ملخص"},
        )
        self.assertIsInstance(result, ArticleDetailResult)
        self.assertEqual(result.model_dump(mode="json"), response)

    async def test_get_article_returns_typed_detail(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)
        article_id = "11111111-1111-1111-1111-111111111111"
        response = self._article_detail(article_id)

        with patch(
            "albayan_mcp.tools.articles.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await fake_server.tools["get_article"](article_id)

        get.assert_awaited_once_with(f"/api/v1/articles/{article_id}")
        self.assertIsInstance(result, ArticleDetailResult)

    async def test_update_article_metadata_patches_only_supplied_fields(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)
        article_id = "11111111-1111-1111-1111-111111111111"
        response = self._article_detail(article_id)
        response["abstract"] = ""

        with patch(
            "albayan_mcp.tools.articles.api_patch_object",
            new=AsyncMock(return_value=response),
        ) as patch_article:
            result = await fake_server.tools["update_article_metadata"](
                article_id,
                2,
                abstract="",
            )

        patch_article.assert_awaited_once_with(
            f"/api/v1/articles/{article_id}",
            json={"base_revision": 2, "abstract": ""},
        )
        self.assertEqual(result.abstract, "")

    async def test_update_article_metadata_requires_at_least_one_field(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)

        with self.assertRaises(ToolError):
            await fake_server.tools["update_article_metadata"](
                "11111111-1111-1111-1111-111111111111",
                2,
            )

    def test_article_tool_schemas_do_not_expose_authors_or_submission(self) -> None:
        fake_server = FakeServer()
        register_article_tools(fake_server)

        self.assertNotIn("submit_article", fake_server.tools)
        for name in ("create_article", "update_article_metadata"):
            annotations = fake_server.tools[name].__annotations__
            self.assertNotIn("authors", annotations)

    async def test_real_discovery_publishes_typed_draft_only_article_tools(self) -> None:
        server = MCPServer("article-schema-test")
        register_article_tools(server)
        published = {tool.name: tool for tool in await server.list_tools()}

        self.assertNotIn("submit_article", published)
        self.assertNotIn("delete_article", published)
        for name, expected_properties in (
            ("create_article", {"title", "abstract"}),
            ("get_article", {"article_id"}),
            (
                "update_article_metadata",
                {"article_id", "base_revision", "title", "abstract"},
            ),
        ):
            with self.subTest(name=name):
                schema = published[name].input_schema
                self.assertEqual(set(schema["properties"]), expected_properties)
                self.assertNotIn("authors", schema["properties"])
                self.assertIsNotNone(published[name].output_schema)
        update_properties = published["update_article_metadata"].input_schema[
            "properties"
        ]
        self.assertEqual(update_properties["title"]["type"], "string")
        self.assertEqual(update_properties["abstract"]["type"], "string")
        detail_schema = published["get_article"].output_schema
        self.assertEqual(detail_schema["properties"]["id"]["format"], "uuid")
        self.assertEqual(
            detail_schema["properties"]["created_at"]["format"],
            "date-time",
        )
        version_schema = detail_schema["$defs"]["ArticleVersionResult"]
        self.assertEqual(version_schema["properties"]["id"]["format"], "uuid")

    async def test_real_mcp_call_accepts_an_abstract_only_update(self) -> None:
        server = MCPServer("article-call-test")
        register_article_tools(server)
        article_id = "11111111-1111-1111-1111-111111111111"
        response = self._article_detail(article_id)
        response["abstract"] = "ملخص جديد"

        with patch(
            "albayan_mcp.tools.articles.api_patch_object",
            new=AsyncMock(return_value=response),
        ) as patch_article:
            result = await server.call_tool(
                "update_article_metadata",
                {"article_id": article_id, "base_revision": 2, "abstract": "ملخص جديد"},
            )

        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content["abstract"], "ملخص جديد")
        patch_article.assert_awaited_once_with(
            f"/api/v1/articles/{article_id}",
            json={"base_revision": 2, "abstract": "ملخص جديد"},
        )


if __name__ == "__main__":
    unittest.main()
