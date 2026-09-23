from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from albayan_dev_mcp.client import DevHttpClient
from albayan_dev_mcp.settings import Settings


def register_health_tool(server: MCPServer, *, settings: Settings) -> None:
    @server.tool(
        name="dev_health",
        title="Check development service health",
        description=(
            "Check which configured Al-Bayan development services are reachable. Missing URLs or "
            "unreachable services are returned as explicit blockers with a human_action field."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )
    async def dev_health() -> dict[str, Any]:
        client = DevHttpClient(settings)
        services: dict[str, Any] = {}
        for name in ("albayan", "burhan", "butex"):
            services[name] = await client.probe(name)  # type: ignore[arg-type]
        blockers = [
            {"service": name, **status}
            for name, status in services.items()
            if status.get("blocked")
        ]
        return {
            "ok": not blockers,
            "services": services,
            "blockers": blockers,
            "note": (
                "This connector is development-only. If a required capability is unavailable, "
                "report the blocker and human_action instead of guessing or requesting production access."
            ),
        }
