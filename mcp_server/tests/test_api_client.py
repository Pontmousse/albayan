from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.server.mcpserver.exceptions import ToolError

from albayan_mcp import api_client


class ApiClientTests(unittest.IsolatedAsyncioTestCase):
    def _response(self, data: object, *, status_code: int = 200) -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.raise_for_status = MagicMock()
        response.json = MagicMock(return_value=data)
        return response

    def _async_client(self, response: MagicMock) -> tuple[MagicMock, AsyncMock]:
        request = AsyncMock(return_value=response)
        client = MagicMock()
        client.request = request
        manager = MagicMock()
        manager.__aenter__ = AsyncMock(return_value=client)
        manager.__aexit__ = AsyncMock(return_value=None)
        async_client = MagicMock(return_value=manager)
        return async_client, request

    async def test_http_path_forwards_mcp_request_token(self) -> None:
        response = self._response({"ok": True})
        async_client, request = self._async_client(response)

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="alb_hosted"),
        ), patch.object(
            api_client.settings,
            "albayan_api_url",
            "http://api.test",
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            data = await api_client.api_request("GET", "/api/v1/users/me")

        self.assertEqual(data, {"ok": True})
        async_client.assert_called_once_with(base_url="http://api.test", timeout=30.0)
        request.assert_awaited_once()
        self.assertEqual(
            request.await_args.kwargs["headers"]["Authorization"],
            "Bearer alb_hosted",
        )

    async def test_stdio_path_uses_albayan_agent_token(self) -> None:
        response = self._response({"ok": True})
        async_client, request = self._async_client(response)

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=None,
        ), patch.object(
            api_client.settings,
            "albayan_agent_token",
            "alb_stdio",
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            data = await api_client.api_request("GET", "/api/v1/users/me")

        self.assertEqual(data, {"ok": True})
        self.assertEqual(
            request.await_args.kwargs["headers"]["Authorization"],
            "Bearer alb_stdio",
        )

    async def test_missing_credentials_raises_clean_error(self) -> None:
        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=None,
        ), patch.object(
            api_client.settings,
            "albayan_agent_token",
            "",
        ):
            with self.assertRaises(RuntimeError) as ctx:
                await api_client.api_request("GET", "/api/v1/users/me")

        self.assertIn("لا يوجد مفتاح مصادقة", str(ctx.exception))

    async def test_object_helper_accepts_object(self) -> None:
        with patch(
            "albayan_mcp.api_client.api_request",
            new=AsyncMock(return_value={"id": "1"}),
        ):
            self.assertEqual(await api_client.api_get_object("/x"), {"id": "1"})

    async def test_object_helper_rejects_list(self) -> None:
        with patch(
            "albayan_mcp.api_client.api_request",
            new=AsyncMock(return_value=[]),
        ):
            with self.assertRaises(RuntimeError):
                await api_client.api_get_object("/x")

    async def test_list_helper_accepts_list(self) -> None:
        with patch(
            "albayan_mcp.api_client.api_request",
            new=AsyncMock(return_value=[{"id": "1"}]),
        ):
            self.assertEqual(await api_client.api_get_list("/x"), [{"id": "1"}])

    async def test_list_helper_rejects_object(self) -> None:
        with patch(
            "albayan_mcp.api_client.api_request",
            new=AsyncMock(return_value={"id": "1"}),
        ):
            with self.assertRaises(RuntimeError):
                await api_client.api_get_list("/x")

    async def test_204_returns_none(self) -> None:
        response = self._response(None, status_code=204)
        async_client, _ = self._async_client(response)

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="http-token"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            self.assertIsNone(await api_client.api_request("DELETE", "/x"))

    async def test_revision_conflict_becomes_safe_structured_tool_error(self) -> None:
        response = self._response(
            {
                "detail": {
                    "code": "revision_conflict",
                    "message": "تغيرت الجلسة؛ أعد قراءتها.",
                    "current_revision": 8,
                }
            },
            status_code=409,
        )
        async_client, _ = self._async_client(response)

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="caller-token"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            with self.assertRaises(api_client.BackendApiError) as ctx:
                await api_client.api_request(
                    "POST", "/api/v1/articles/a/session/commands"
                )

        self.assertEqual(
            json.loads(str(ctx.exception)),
            {
                "status": 409,
                "code": "revision_conflict",
                "message": "تغيرت الجلسة؛ أعد قراءتها.",
                "current_revision": 8,
            },
        )
        self.assertIsInstance(ctx.exception, ToolError)
        response.raise_for_status.assert_not_called()

    async def test_validation_details_are_not_exposed_verbatim(self) -> None:
        response = self._response(
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "command", "field_id"],
                        "msg": "Field required",
                        "input": {"secret": "must-not-leak"},
                    }
                ]
            },
            status_code=422,
        )
        async_client, _ = self._async_client(response)

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="caller-token"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            with self.assertRaises(api_client.BackendApiError) as ctx:
                await api_client.api_request("POST", "/api/v1/example")

        payload = json.loads(str(ctx.exception))
        self.assertEqual(payload["status"], 422)
        self.assertEqual(payload["code"], "validation_error")
        self.assertIn("body.command.field_id", payload["message"])
        self.assertIn("Field required", payload["message"])
        self.assertNotIn("must-not-leak", str(ctx.exception))

    async def test_session_post_forwards_caller_bearer_and_payload(self) -> None:
        response = self._response({"ok": True})
        async_client, request = self._async_client(response)
        payload = {
            "command_id": "command-1",
            "base_revision": 3,
            "command": {"op": "remove_block", "block_id": "block-1"},
        }

        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="caller-bearer"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            await api_client.api_post_object(
                "/api/v1/articles/article-1/session/commands",
                json=payload,
            )

        self.assertEqual(
            request.await_args.kwargs["headers"]["Authorization"],
            "Bearer caller-bearer",
        )
        self.assertEqual(request.await_args.kwargs["json"], payload)

    async def test_binary_get_forwards_bearer_and_preserves_identity_headers(self) -> None:
        response = self._response(None)
        response.content = b"%PDF"
        response.headers = {
            "content-type": "application/pdf",
            "x-albayan-compile-id": "compile-1",
        }
        async_client, request = self._async_client(response)
        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="caller-token"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            result = await api_client.api_get_bytes("/article/pdf")

        self.assertEqual(result.content, b"%PDF")
        self.assertEqual(result.content_type, "application/pdf")
        self.assertEqual(result.headers["x-albayan-compile-id"], "compile-1")
        self.assertEqual(
            request.await_args.kwargs["headers"]["Authorization"],
            "Bearer caller-token",
        )

    async def test_document_issues_are_allow_listed_in_tool_error(self) -> None:
        response = self._response(
            {
                "detail": {
                    "code": "invalid_document",
                    "message": "تعذر تصدير المستند.",
                    "issues": [
                        {
                            "code": "empty_image",
                            "path": "blocks[0]",
                            "blockId": "block-1",
                            "secret": "not-forwarded",
                        }
                    ],
                }
            },
            status_code=422,
        )
        async_client, _ = self._async_client(response)
        with patch(
            "albayan_mcp.api_client.get_access_token",
            return_value=SimpleNamespace(token="caller-token"),
        ), patch(
            "albayan_mcp.api_client.httpx.AsyncClient",
            async_client,
        ):
            with self.assertRaises(api_client.BackendApiError) as ctx:
                await api_client.api_request("POST", "/compile")

        payload = json.loads(str(ctx.exception))
        self.assertEqual(
            payload["issues"],
            [
                {
                    "code": "empty_image",
                    "path": "blocks[0]",
                    "blockId": "block-1",
                }
            ],
        )
        self.assertNotIn("not-forwarded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
