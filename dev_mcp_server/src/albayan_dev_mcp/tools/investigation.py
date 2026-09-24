from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from albayan_dev_mcp.investigation import (
    InvestigationRunner,
    capabilities,
    list_suites,
)
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TraceSource

ModelTier = Literal["heuristic", "cheap", "medium"]
BrowserObservation = Literal["not_checked", "passed", "failed", "blocked"]


def register_investigation_tools(
    server: MCPServer,
    *,
    settings: Settings,
    trace_source: TraceSource | None = None,
) -> None:
    def runner() -> InvestigationRunner:
        return InvestigationRunner(settings, trace_source=trace_source)

    @server.tool(
        name="dev_capabilities",
        title="Discover developer diagnostic capabilities",
        description=(
            "Inspect configured development-service and diagnostic capabilities before planning an investigation. "
            "This reports configuration state, named suites, supported Burhan tiers, browser-observation hints, "
            "and exact human actions for missing capabilities. Use dev_health separately for live reachability."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_capabilities() -> dict[str, Any]:
        return capabilities(settings)

    @server.tool(
        name="dev_regression_suites",
        title="List named developer regression suites",
        description=(
            "List reusable Phase 4 regression suites and whether they are deterministic, live, and suitable only "
            "for opt-in live execution. Discovery itself is offline and does not call development services."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_regression_suites() -> dict[str, Any]:
        suites = list_suites()
        return {
            "ok": True,
            "suite_count": len(suites),
            "suites": suites,
            "ci_note": (
                "Suite registration/schema checks run offline in mandatory CI. Live service execution is opt-in; "
                "LLM-backed tier comparisons are not mandatory merge gates."
            ),
        }

    @server.tool(
        name="dev_run_regression_suite",
        title="Run one named developer regression suite",
        description=(
            "Run a bounded named regression suite through existing specialized diagnostics. Results identify the first "
            "observable failing stage, likely owning service with an uncertainty note, trace IDs, blockers, missing "
            "observations, and human actions. The burhan-tier-comparison suite can consume provider budget."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_run_regression_suite(
        suite_name: Annotated[str, Field(min_length=1, max_length=100)],
        model_tier: Annotated[
            ModelTier,
            Field(description="Tier used by fixture suites; ignored by the all-tier comparison suite."),
        ] = "heuristic",
        max_fixtures: Annotated[
            int,
            Field(ge=1, le=50, description="Additional per-call bound; server report limits still apply."),
        ] = 50,
    ) -> dict[str, Any]:
        return await runner().run_suite(
            suite_name=suite_name,
            model_tier=model_tier,
            max_fixtures=max_fixtures,
        )

    @server.tool(
        name="dev_investigation_report",
        title="Run an evidence-oriented developer investigation",
        description=(
            "Run a named regression suite and return the stable Phase 4 investigation-report schema. Optionally compare "
            "a second Burhan model tier. Browser evidence remains external: use Playwright MCP separately and pass only "
            "a bounded observation summary here. Ownership is inferred only from observable stage boundaries and is "
            "explicitly not proof of root cause."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_investigation_report(
        suite_name: Annotated[str, Field(min_length=1, max_length=100)],
        model_tier: ModelTier = "heuristic",
        compare_model_tier: Annotated[
            ModelTier | None,
            Field(description="Optional second controlled model tier for compact before/after comparison."),
        ] = None,
        require_browser: Annotated[
            bool,
            Field(description="True only when the requested conclusion genuinely requires browser/UI evidence."),
        ] = False,
        browser_observation: Annotated[
            BrowserObservation,
            Field(description="External Playwright/agent observation; Dev MCP never runs Playwright itself."),
        ] = "not_checked",
        browser_note: Annotated[
            str | None,
            Field(max_length=1000, description="Optional short external browser-evidence summary; never include secrets."),
        ] = None,
    ) -> dict[str, Any]:
        return await runner().investigation_report(
            suite_name=suite_name,
            model_tier=model_tier,
            compare_model_tier=compare_model_tier,
            require_browser=require_browser,
            browser_observation=browser_observation,
            browser_note=browser_note,
        )
