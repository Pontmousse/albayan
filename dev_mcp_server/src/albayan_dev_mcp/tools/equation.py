from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from albayan_dev_mcp.equation import (
    MODEL_TIERS,
    EquationDiagnosticClient,
    compare_reports,
    fixture_by_id,
    load_equation_fixtures,
    stage_matrix,
)
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TraceSource, resolve_trace_id

ModelTier = Literal["heuristic", "cheap", "medium"]


def register_equation_tools(
    server: MCPServer,
    *,
    settings: Settings,
    trace_source: TraceSource | None = None,
) -> None:
    def client() -> EquationDiagnosticClient:
        return EquationDiagnosticClient(settings, trace_source=trace_source)

    @server.tool(
        name="dev_equation_inspect",
        title="Inspect one equation pipeline run",
        description=(
            "Run canonical English LaTeX through the real Al-Bayan/Burhan/Document2/BuTeX "
            "diagnostic pipeline without persisting article state. Returns authoritative stages, "
            "trace linkage, explicit unavailable stages, and a separate browser-validation gap. "
            "cheap/medium tiers may consume the configured Burhan model provider budget."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_equation_inspect(
        latex: Annotated[str, Field(min_length=1, max_length=10_000)],
        model_tier: Annotated[
            ModelTier,
            Field(description="Burhan tier: heuristic, cheap, or medium."),
        ] = "heuristic",
        display: Annotated[
            bool,
            Field(description="Treat the equation as display math; otherwise inline math."),
        ] = False,
        trace_id: Annotated[
            str | None,
            Field(description="Optional existing diagnostic correlation ID."),
        ] = None,
    ) -> dict[str, Any]:
        return await client().inspect(
            latex=latex,
            display=display,
            model_tier=model_tier,
            trace_id=trace_id,
        )

    @server.tool(
        name="dev_equation_compare_model_tiers",
        title="Compare Burhan equation model tiers",
        description=(
            "Run the same equation through heuristic, cheap, and medium tiers and compare mappings, "
            "structured outputs, warnings, reverse LaTeX, timing, and downstream BuTeX editor import. "
            "All three calls share one trace_id. cheap/medium may incur provider cost."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_equation_compare_model_tiers(
        latex: Annotated[str, Field(min_length=1, max_length=10_000)],
        display: bool = False,
        trace_id: Annotated[str | None, Field(description="Optional shared correlation ID.")] = None,
    ) -> dict[str, Any]:
        shared_trace = resolve_trace_id(trace_id)
        reports: dict[str, dict[str, Any]] = {}
        diagnostic_client = client()
        for tier in MODEL_TIERS:
            reports[tier] = await diagnostic_client.inspect(
                latex=latex,
                display=display,
                model_tier=tier,
                trace_id=shared_trace,
            )
        return {
            "ok": all(not report.get("blocked", False) for report in reports.values()),
            "trace_id": shared_trace,
            "latex": latex,
            "display": display,
            "comparison": compare_reports(reports),
        }

    @server.tool(
        name="dev_equation_run_fixture",
        title="Run one equation regression fixture",
        description=(
            "Load one machine-readable Phase 3 fixture and run it through the real equation diagnostic pipeline. "
            "Known-failure metadata is descriptive and never changes the observed result."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_equation_run_fixture(
        fixture_id: Annotated[str, Field(min_length=1, max_length=100)],
        model_tier: ModelTier = "heuristic",
    ) -> dict[str, Any]:
        fixture = fixture_by_id(fixture_id)
        if fixture is None:
            available = [row["id"] for row in load_equation_fixtures()]
            return {
                "ok": False,
                "blocked": True,
                "reason": "fixture_not_found",
                "fixture_id": fixture_id,
                "available_fixture_ids": available,
                "human_action": "Choose one of the fixture IDs returned by this tool.",
            }
        report = await client().inspect(
            latex=fixture["source"],
            display=fixture["display"],
            model_tier=model_tier,
        )
        return {
            "ok": report.get("ok"),
            "fixture": fixture,
            "stage_matrix": stage_matrix(report),
            "report": report,
        }

    @server.tool(
        name="dev_equation_run_suite",
        title="Run the equation regression fixture suite",
        description=(
            "Run a bounded set of equation fixtures and return a compact stage matrix. "
            "Use heuristic by default for deterministic low-cost regression; cheap/medium can consume provider budget."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_equation_run_suite(
        model_tier: ModelTier = "heuristic",
        tag: Annotated[
            str | None,
            Field(description="Optional fixture tag such as adjacency, derivative, spacing, or regression."),
        ] = None,
        max_fixtures: Annotated[int, Field(ge=1, le=50)] = 50,
    ) -> dict[str, Any]:
        fixtures = load_equation_fixtures()
        if tag:
            fixtures = [fixture for fixture in fixtures if tag in fixture["tags"]]
        fixtures = fixtures[:max_fixtures]

        rows: list[dict[str, Any]] = []
        diagnostic_client = client()
        for fixture in fixtures:
            report = await diagnostic_client.inspect(
                latex=fixture["source"],
                display=fixture["display"],
                model_tier=model_tier,
            )
            matrix = stage_matrix(report)
            failed = [name for name, status in matrix.items() if status == "fail"]
            unavailable = [name for name, status in matrix.items() if status == "unavailable"]
            rows.append(
                {
                    "id": fixture["id"],
                    "source": fixture["source"],
                    "display": fixture["display"],
                    "support_class": fixture["support_class"],
                    "known_failure": fixture.get("known_failure"),
                    "ok": report.get("ok"),
                    "blocked": report.get("blocked", False),
                    "partial": report.get("partial", False),
                    "trace_id": report.get("trace_id"),
                    "stage_matrix": matrix,
                    "failed_stages": failed,
                    "unavailable_stages": unavailable,
                }
            )

        return {
            "ok": all(row["ok"] is True for row in rows) if rows else True,
            "model_tier": model_tier,
            "tag": tag,
            "fixture_count": len(rows),
            "rows": rows,
        }
