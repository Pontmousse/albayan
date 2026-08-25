from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from albayan_mcp import server as server_module
from albayan_mcp.tools.profile import ProfileResult, register_profile_tools


class FakeServer:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, *, name: str, **kwargs: object):
        def decorator(func):
            self.tools[name] = func
            return func

        return decorator


class ProfileToolTests(unittest.IsolatedAsyncioTestCase):
    def test_create_server_exposes_get_my_profile(self) -> None:
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

    async def test_get_my_profile_calls_backend_and_returns_structured_output(self) -> None:
        fake_server = FakeServer()
        register_profile_tools(fake_server)

        with patch(
            "albayan_mcp.tools.profile.api_get_object",
            new=AsyncMock(
                return_value={
                    "id": "user-1",
                    "email": "user@example.com",
                    "full_name": "User One",
                    "affiliation": "Al-Bayan",
                    "bio": None,
                }
            ),
        ) as api_get_object:
            result = await fake_server.tools["get_my_profile"]()

        api_get_object.assert_awaited_once_with("/api/v1/users/me")
        self.assertIsInstance(result, ProfileResult)
        self.assertEqual(
            result.model_dump(),
            {
                "id": "user-1",
                "email": "user@example.com",
                "full_name": "User One",
                "affiliation": "Al-Bayan",
            },
        )


if __name__ == "__main__":
    unittest.main()
