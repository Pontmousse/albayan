from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl

from albayan_mcp.settings import settings
from albayan_mcp.token_verifier import PassThroughTokenVerifier
from albayan_mcp.tools.articles import register_article_tools
from albayan_mcp.tools.profile import register_profile_tools


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

    # Tool implementations belong under tools/; keep this module composition-only.
    register_profile_tools(server)
    register_article_tools(server)

    return server
