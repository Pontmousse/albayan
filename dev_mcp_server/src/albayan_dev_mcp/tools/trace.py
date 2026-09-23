from __future__ import annotations

from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from albayan_dev_mcp.trace import TraceSource, validate_trace_id


def register_trace_tools(server: MCPServer, *, trace_source: TraceSource) -> None:
    @server.tool(
        name="dev_get_trace",
        title="Inspect one development trace",
        description=(
            "Return the ordered events currently available for one development trace. "
            "The default Phase-2 source is process-local and therefore reports downstream "
            "service-log coverage as a known gap until a centralized adapter is configured."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )
    def dev_get_trace(
        trace_id: Annotated[
            str,
            Field(description="Correlation identifier returned by another developer diagnostic tool."),
        ],
    ) -> dict[str, Any]:
        try:
            normalized = validate_trace_id(trace_id)
        except ValueError as exc:
            return {
                "ok": False,
                "blocked": True,
                "reason": "invalid_trace_id",
                "message": str(exc),
                "human_action": "Use the trace_id returned by a developer MCP diagnostic operation.",
            }

        events = trace_source.get_trace(normalized)
        if not events:
            return {
                "ok": False,
                "blocked": False,
                "reason": "trace_not_found",
                "trace_id": normalized,
                "source": trace_source.name,
                "persistent": trace_source.persistent,
                "human_action": (
                    "The current trace source may have restarted or evicted this trace. "
                    "Rerun the diagnostic, or configure a persistent development trace backend."
                ),
            }

        return {
            "ok": True,
            "blocked": False,
            "trace_id": normalized,
            "source": trace_source.name,
            "persistent": trace_source.persistent,
            "coverage": list(trace_source.coverage),
            "partial": "downstream_services" not in trace_source.coverage,
            "events": [event.as_dict() for event in events],
            "missing_stages": (
                ["centralized_downstream_service_events"]
                if "downstream_services" not in trace_source.coverage
                else []
            ),
            "human_action": (
                "Configure a centralized development trace adapter when Railway/log aggregation "
                "is available to include backend, Burhan, and BuTeX service events."
                if "downstream_services" not in trace_source.coverage
                else None
            ),
        }

    @server.tool(
        name="dev_list_recent_traces",
        title="List recent development traces",
        description=(
            "List bounded recent trace summaries from the configured development trace source. "
            "No request/response bodies or secrets are returned."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )
    def dev_list_recent_traces(
        limit: Annotated[
            int,
            Field(default=20, ge=1, le=100, description="Maximum trace summaries to return."),
        ] = 20,
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "blocked": False,
            "source": trace_source.name,
            "persistent": trace_source.persistent,
            "coverage": list(trace_source.coverage),
            "traces": trace_source.list_recent(limit=limit),
        }
