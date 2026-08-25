from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
            return_value=SimpleNamespace(token="http-token"),
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
            "Bearer http-token",
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


if __name__ == "__main__":
    unittest.main()
