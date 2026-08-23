from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl

from albayan_mcp.api_client import api_get
from albayan_mcp.settings import settings
from albayan_mcp.token_verifier import PassThroughTokenVerifier


def create_server() -> MCPServer:
    auth = None
    token_verifier = None

    if settings.oauth_enabled:
        from mcp.server.auth.settings import AuthSettings

        auth = AuthSettings(
            issuer_url=AnyHttpUrl(settings.clerk_issuer_url),
            resource_server_url=AnyHttpUrl(settings.mcp_resource_url),
            required_scopes=["profile:read", "articles:read"],
        )
        token_verifier = PassThroughTokenVerifier()

    server = MCPServer(
        "albayan",
        title="مجلة البيان",
        instructions=(
            "خادم MCP لمجلة البيان. يستدعي واجهة FastAPI فقط — "
            "المصادقة والتفويض على الخادم الخلفي."
        ),
        auth=auth,
        token_verifier=token_verifier,
    )

    @server.tool(
        name="get_my_profile",
        title="ملفي الشخصي",
        description="قراءة الملف الشخصي للمستخدم الحالي من مجلة البيان.",
    )
    async def get_my_profile() -> str:
        profile = await api_get("/api/v1/users/me")
        summary = {
            "id": profile.get("id"),
            "email": profile.get("email"),
            "full_name": profile.get("full_name"),
            "affiliation": profile.get("affiliation"),
        }
        return json.dumps(summary, ensure_ascii=False)

    return server
