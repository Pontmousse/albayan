from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from albayan_dev_mcp.client import DevHttpClient
from albayan_dev_mcp.settings import ServiceName, Settings
from albayan_dev_mcp.trace import TraceSource

Method = Literal["GET", "HEAD", "OPTIONS"]


def register_http_tool(
    server: MCPServer,
    *,
    settings: Settings,
    trace_source: TraceSource | None = None,
) -> None:
    @server.tool(
        name="dev_http_request",
        title="Request a configured development service",
        description=(
            "Read-only HTTP diagnostic against one explicitly configured development service. "
            "The target host is selected by service name; arbitrary URLs and redirects are not followed. "
            "A trace_id is generated automatically unless supplied for correlation/replay. "
            "Use specialized diagnostic tools when they exist."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )
    async def dev_http_request(
        service: Annotated[
            ServiceName,
            Field(description="Configured development service: albayan, burhan, or butex."),
        ],
        path: Annotated[
            str,
            Field(description="Absolute path on the configured service origin, e.g. /health. No URL or query string."),
        ] = "/",
        method: Annotated[
            Method,
            Field(description="Read-only HTTP method. POST is intentionally unavailable in the generic escape hatch."),
        ] = "GET",
        query: Annotated[
            dict[str, str | int | float | bool] | None,
            Field(description="Optional query parameters. Secrets must not be supplied here."),
        ] = None,
        trace_id: Annotated[
            str | None,
            Field(
                description=(
                    "Optional existing correlation ID. Omit to generate one. "
                    "This value is diagnostic only and never authorizes access."
                )
            ),
        ] = None,
    ) -> dict[str, Any]:
        client = DevHttpClient(settings, trace_source=trace_source)
        try:
            return await client.request(
                service=service,
                method=method,
                path=path,
                query=query,
                trace_id=trace_id,
            )
        except ValueError as exc:
            return {
                "ok": False,
                "blocked": True,
                "reason": "invalid_request_target",
                "message": str(exc),
                "human_action": (
                    "Use only a path on one of the configured development services and a valid trace_id. "
                    "If a different service is required, ask the human developer to expose/configure it explicitly."
                ),
            }
