from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.tools.health import register_health_tool
from albayan_dev_mcp.tools.http import register_http_tool


def create_server(settings: Settings | None = None) -> MCPServer:
    runtime_settings = settings or Settings()
    server = MCPServer(
        "albayan-dev",
        title="Al-Bayan Developer Diagnostics",
        instructions=(
            "Developer-only diagnostic MCP for trusted Al-Bayan coding agents. "
            "Prefer specialized read-only diagnostic tools. Never infer unavailable runtime facts. "
            "When a tool returns blocked=true, surface its reason and human_action to the human developer. "
            "Do not request production credentials as a workaround for missing development access."
        ),
    )
    register_health_tool(server, settings=runtime_settings)
    register_http_tool(server, settings=runtime_settings)
    return server
