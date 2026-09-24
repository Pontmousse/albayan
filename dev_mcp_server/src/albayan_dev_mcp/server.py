from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl

from albayan_dev_mcp.auth import DeveloperMetadataTokenVerifier
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.tools.equation import register_equation_tools
from albayan_dev_mcp.tools.health import register_health_tool
from albayan_dev_mcp.tools.http import register_http_tool
from albayan_dev_mcp.tools.trace import register_trace_tools
from albayan_dev_mcp.trace import InMemoryTraceSource, TraceSource


def create_server(
    settings: Settings | None = None,
    *,
    trace_source: TraceSource | None = None,
) -> MCPServer:
    runtime_settings = settings or Settings()
    runtime_trace_source = trace_source or InMemoryTraceSource(
        max_traces=runtime_settings.dev_mcp_trace_max_traces,
        max_events_per_trace=runtime_settings.dev_mcp_trace_max_events_per_trace,
    )
    auth = None
    token_verifier = None

    # Local stdio can run without OAuth. Remote Streamable HTTP is fail-closed
    # by __main__.py unless this complete auth configuration is present.
    if runtime_settings.remote_auth_configured:
        from mcp.server.auth.settings import AuthSettings

        auth = AuthSettings(
            issuer_url=AnyHttpUrl(runtime_settings.clerk_issuer_url.strip()),
            resource_server_url=AnyHttpUrl(runtime_settings.dev_mcp_resource_url.strip()),
            required_scopes=["openid", "profile", "email"],
        )
        token_verifier = DeveloperMetadataTokenVerifier(
            clerk_secret_key=runtime_settings.clerk_secret_key.strip()
        )

    server = MCPServer(
        "albayan-dev",
        title="Al-Bayan Developer Diagnostics",
        instructions=(
            "Developer-only diagnostic MCP for trusted Al-Bayan coding agents. "
            "Remote access requires Clerk authentication and a Clerk user whose "
            "public_metadata.developer is exactly true. "
            "Prefer specialized read-only diagnostic tools. For equation bugs, use the equation inspection/fixture tools "
            "before the generic HTTP escape hatch and distinguish deterministic headless BuTeX evidence from browser evidence. "
            "Correlate operations with trace_id when available. Never infer unavailable runtime facts. "
            "When a tool returns blocked=true or partial=true, surface its reason, missing stages, and human_action "
            "to the human developer. Do not request production credentials as a workaround for missing development access."
        ),
        auth=auth,
        token_verifier=token_verifier,
    )
    register_health_tool(server, settings=runtime_settings)
    register_http_tool(
        server,
        settings=runtime_settings,
        trace_source=runtime_trace_source,
    )
    register_trace_tools(server, trace_source=runtime_trace_source)
    register_equation_tools(
        server,
        settings=runtime_settings,
        trace_source=runtime_trace_source,
    )
    return server
