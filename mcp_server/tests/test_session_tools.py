from __future__ import annotations

import unittest
import uuid
from unittest.mock import AsyncMock, patch

from pydantic import TypeAdapter

from albayan_mcp.api_client import BackendApiError
from albayan_mcp.schemas.document2 import DocumentCommand
from albayan_mcp.tools.sessions import (
    SessionBlocksResult,
    SessionCommandResult,
    SessionOutlineResult,
    SessionSaveResult,
    register_session_tools,
)
from tests.test_profile_tools import FakeServer


class SessionToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server = FakeServer()
        register_session_tools(self.server)
        self.article_id = uuid.uuid4()

    def test_registers_four_discoverable_tools_with_descriptions(self) -> None:
        self.assertEqual(
            set(self.server.tools),
            {
                "get_session_outline",
                "get_session_blocks",
                "apply_session_command",
                "save_session",
            },
        )
        for name in self.server.tools:
            description = self.server.tool_options[name].get("description")
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 40)

    async def test_outline_calls_fastapi_and_returns_typed_result(self) -> None:
        response = {
            "revision": 4,
            "last_saved_revision": 2,
            "outline": [
                {
                    "id": "block_1",
                    "kind": "paragraph",
                    "command": "paragraph",
                    "excerpt": "نص المقال",
                }
            ],
        }
        with patch(
            "albayan_mcp.tools.sessions.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_session_outline"](self.article_id)

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/session/outline"
        )
        self.assertIsInstance(result, SessionOutlineResult)
        self.assertEqual(result.model_dump(), response)

    async def test_blocks_preserve_known_ids_and_future_fields(self) -> None:
        response = {
            "revision": 5,
            "last_saved_revision": 3,
            "blocks": [
                {
                    "id": "list_1",
                    "command": "itemize",
                    "future_worker_field": {"kept": True},
                    "items": [
                        {
                            "id": "item_1",
                            "inline_ids": {
                                "field_id": "field_1",
                                "tokens": [
                                    {
                                        "id": "token_1",
                                        "kind": "text",
                                        "start": 0,
                                        "end": 3,
                                    }
                                ],
                                "future_inline_field": "kept",
                            },
                        }
                    ],
                }
            ],
        }
        with patch(
            "albayan_mcp.tools.sessions.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_session_blocks"](self.article_id)

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/session/blocks"
        )
        self.assertIsInstance(result, SessionBlocksResult)
        self.assertEqual(result.model_dump(exclude_none=True), response)

    async def test_apply_posts_only_fastapi_envelope_and_returns_typed_result(self) -> None:
        command_id = uuid.uuid4()
        command = TypeAdapter(DocumentCommand).validate_python(
            {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "token": {"kind": "text", "text": "إضافة"},
                "anchor": {"end": True},
            }
        )
        response = {
            "ok": True,
            "revision": 6,
            "last_saved_revision": 3,
            "document": {"node_type": "DocumentObject", "blocks": [{"id": "block_1"}]},
            "affected_block_ids": ["block_1"],
        }
        with patch(
            "albayan_mcp.tools.sessions.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            result = await self.server.tools["apply_session_command"](
                self.article_id,
                command_id,
                5,
                command,
            )

        post.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/session/commands",
            json={
                "command_id": str(command_id),
                "base_revision": 5,
                "command": {
                    "op": "insert_inline_token",
                    "field_id": "field_1",
                    "token": {"kind": "text", "text": "إضافة"},
                    "anchor": {"end": True},
                },
            },
        )
        self.assertIsInstance(result, SessionCommandResult)
        self.assertEqual(result.model_dump(exclude_none=True), response)

    async def test_apply_preserves_explicit_null_asset(self) -> None:
        command = TypeAdapter(DocumentCommand).validate_python(
            {"op": "update_figure", "block_id": "figure_1", "asset_id": None}
        )
        response = {
            "ok": True,
            "revision": 2,
            "last_saved_revision": 1,
            "document": {"blocks": [{"id": "figure_1"}]},
            "affected_block_ids": ["figure_1"],
        }
        with patch(
            "albayan_mcp.tools.sessions.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            await self.server.tools["apply_session_command"](
                self.article_id,
                uuid.uuid4(),
                1,
                command,
            )

        sent_command = post.await_args.kwargs["json"]["command"]
        self.assertIn("asset_id", sent_command)
        self.assertIsNone(sent_command["asset_id"])
        self.assertNotIn("value", sent_command)

    async def test_revision_conflict_propagates_as_tool_error(self) -> None:
        command = TypeAdapter(DocumentCommand).validate_python(
            {"op": "remove_block", "block_id": "block_1"}
        )
        error = BackendApiError(
            status=409,
            code="revision_conflict",
            message="أعد قراءة الجلسة.",
            current_revision=9,
        )
        with patch(
            "albayan_mcp.tools.sessions.api_post_object",
            new=AsyncMock(side_effect=error),
        ):
            with self.assertRaises(BackendApiError) as ctx:
                await self.server.tools["apply_session_command"](
                    self.article_id,
                    uuid.uuid4(),
                    8,
                    command,
                )

        self.assertIn('"code":"revision_conflict"', str(ctx.exception))
        self.assertIn('"current_revision":9', str(ctx.exception))

    async def test_save_posts_without_a_payload(self) -> None:
        response = {"ok": True, "revision": 7, "last_saved_revision": 7}
        with patch(
            "albayan_mcp.tools.sessions.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            result = await self.server.tools["save_session"](self.article_id)

        post.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/session/save"
        )
        self.assertIsInstance(result, SessionSaveResult)
        self.assertEqual(result.model_dump(), response)


if __name__ == "__main__":
    unittest.main()
