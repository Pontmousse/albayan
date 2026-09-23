from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl

from albayan_dev_mcp.auth import DeveloperRoleTokenVerifier
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.tools.health import register_health_tool
from albayan_dev_mcp.tools.http import register_http_tool


def create_server(settings: Settings | None = None) -> MCPServer:
    runtime_settings = settings or Settings()
    auth = None
    token_verifier = None

    if runtime_settings.remote_auth_configured:
        from mcp.server.auth.settings import AuthSettings

        auth = AuthSettings(
            issuer_url=AnyHttpUrl(runtime_settings.clerk_issuer_url.strip()),
            resource_server_url=AnyHttpUrl(runtime_settings.dev_mcp_resource_url.strip()),
            required_scopes=["openid", "profile", "email"],
        )
        token_verifier = DeveloperRoleTokenVerifier(
            clerk_secret_key=runtime_settings.clerk_secret_key.strip()
        )

    server = MCPServer(
        "albayan-dev",
        title="Al-Bayan Developer Diagnostics",
        instructions=(
            "Developer-only diagnostic MCP for trusted Al-Bayan coding agents. "
            "Remote access requires Clerk authentication and a Clerk user whose "
            "public_metadata.role is exactly 'developer'. "
            "Prefer specialized read-only diagnostic tools. Never infer unavailable runtime facts. "
            "When a tool returns blocked=true, surface its reason and human_action to the human developer. "
            "Do not request production credentials as a workaround for missing development access."
        ),
        auth=auth,
        token_verifier=token_verifier,
    )
    register_health_tool(server, settings=runtime_settings)
    register_http_tool(server, settings=runtime_settings)
    return server
