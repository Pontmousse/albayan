from __future__ import annotations

from typing import Any

import pytest

from albayan_dev_mcp.investigation import (
    REPORT_SCHEMA_VERSION,
    InvestigationRunner,
    capabilities,
    compare_suite_runs,
    list_suites,
)
from albayan_dev_mcp.settings import Settings


_STAGE_NAMES = (
    "canonical_input",
    "burhan_conversion",
    "albayan_projection",
    "document2_command",
    "headless_butex_validation",
    "reverse_conversion",
    "browser_validation",
)


class FakeEquationClient:
    def __init__(
        self,
        *,
        fail_stage: str | None = None,
        unavailable_stage: str | None = None,
        blocked: bool = False,
        fail_medium_only: bool = False,
        leak_secret: bool = False,
    ) -> None:
        self.fail_stage = fail_stage
        self.unavailable_stage = unavailable_stage
        self.blocked = blocked
        self.fail_medium_only = fail_medium_only
        self.leak_secret = leak_secret
        self.calls: list[dict[str, Any]] = []

    async def inspect(
        self,
        *,
        latex: str,
        display: bool,
        model_tier: str,
        trace_id: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "latex": latex,
                "display": display,
                "model_tier": model_tier,
                "trace_id": trace_id,
            }
        )
        active_failure = self.fail_stage
        if self.fail_medium_only and model_tier != "medium":
            active_failure = None

        stages: dict[str, dict[str, Any]] = {}
        for name in _STAGE_NAMES:
            if name == "browser_validation":
                stages[name] = {
                    "available": False,
                    "reason": "browser_observation_external",
                    "human_action": "Use Playwright MCP when browser evidence is required.",
                }
            elif name == self.unavailable_stage:
                stages[name] = {
                    "available": False,
                    "reason": "missing_capability",
                    "human_action": f"Expose {name} in the development environment.",
                }
            elif name == active_failure:
                stages[name] = {
                    "available": True,
                    "ok": False,
                    "error": "Bearer secret-token" if self.leak_secret else f"failure at {name}",
                }
            else:
                stages[name] = {"available": True, "ok": True, "data": {"tier": model_tier}}

        return {
            "ok": not self.blocked and active_failure is None,
            "blocked": self.blocked,
            "reason": "missing_configuration" if self.blocked else None,
            "human_action": "Configure ALBAYAN_DEV_TOKEN" if self.blocked else None,
            "trace_id": trace_id,
            "stages": stages,
        }


def test_suite_registry_exposes_named_suites_and_ci_policy() -> None:
    suites = list_suites()
    names = {suite["name"] for suite in suites}
    assert {
        "equations-smoke",
        "equations-adjacency",
        "equations-common-scientific",
        "burhan-tier-comparison",
        "document2-roundtrip",
    } <= names
    assert all(suite["ci_policy"] in {"offline-contract", "opt-in-live"} for suite in suites)
    comparison = next(suite for suite in suites if suite["name"] == "burhan-tier-comparison")
    assert comparison["deterministic"] is False
    assert comparison["ci_policy"] == "opt-in-live"


def test_capabilities_reports_configuration_without_exposing_tokens() -> None:
    settings = Settings(
        _env_file=None,
        albayan_dev_url="https://albayan.dev.example",
        albayan_dev_token="super-secret-token",
        dev_mcp_browser_observation_available=True,
    )
    result = capabilities(settings)
    assert result["schema_version"] == REPORT_SCHEMA_VERSION
    assert result["features"]["equation_inspection"] is True
    assert result["features"]["browser_observation"] is True
    assert result["services"]["albayan"]["token_configured"] is True
    assert "super-secret-token" not in repr(result)


@pytest.mark.asyncio
async def test_deterministic_suite_returns_stage_level_pass_and_trace_links() -> None:
    client = FakeEquationClient()
    runner = InvestigationRunner(
        Settings(_env_file=None, dev_mcp_report_max_rows=10),
        diagnostic_client=client,
    )
    result = await runner.run_suite(
        suite_name="equations-smoke",
        model_tier="heuristic",
        max_fixtures=2,
    )
    assert result["status"] == "passed"
    assert result["fixture_count"] == 2
    assert len(result["trace_ids"]) == 2
    assert all(row["stage_matrix"]["burhan_conversion"] == "pass" for row in result["rows"])
    assert all("browser_validation" in row["optional_missing_observations"] for row in result["rows"])


@pytest.mark.asyncio
async def test_failure_report_assigns_only_boundary_based_likely_owner() -> None:
    client = FakeEquationClient(fail_stage="burhan_conversion")
    runner = InvestigationRunner(Settings(_env_file=None), diagnostic_client=client)
    result = await runner.run_suite(
        suite_name="equations-smoke",
        max_fixtures=1,
    )
    assert result["status"] == "failed"
    assert result["first_failing_stage"] == "burhan_conversion"
    assert result["likely_owning_service"] == "burhan"
    assert "not proof of root cause" in result["ownership_basis"]


@pytest.mark.asyncio
async def test_unavailable_required_stage_is_partial_with_human_action() -> None:
    client = FakeEquationClient(unavailable_stage="headless_butex_validation")
    runner = InvestigationRunner(Settings(_env_file=None), diagnostic_client=client)
    result = await runner.run_suite(
        suite_name="document2-roundtrip",
        max_fixtures=1,
    )
    assert result["status"] == "partial"
    assert "headless_butex_validation" in result["missing_observations"]
    assert any("headless_butex_validation" in action for action in result["human_actions"])


@pytest.mark.asyncio
async def test_blocked_suite_preserves_partial_evidence_and_actionable_guidance() -> None:
    client = FakeEquationClient(blocked=True)
    runner = InvestigationRunner(Settings(_env_file=None), diagnostic_client=client)
    result = await runner.run_suite(
        suite_name="equations-smoke",
        max_fixtures=2,
    )
    assert result["status"] == "blocked"
    assert result["blockers"]
    assert "Configure ALBAYAN_DEV_TOKEN" in result["human_actions"]
    assert len(result["trace_ids"]) == 2


@pytest.mark.asyncio
async def test_investigation_report_has_stable_schema_and_browser_gap_semantics() -> None:
    client = FakeEquationClient()
    runner = InvestigationRunner(Settings(_env_file=None), diagnostic_client=client)
    report = await runner.investigation_report(
        suite_name="equations-smoke",
        require_browser=True,
        browser_observation="not_checked",
    )
    assert report["schema_version"] == REPORT_SCHEMA_VERSION
    assert report["problem_reproduced"] is False
    assert report["regression_status"] == "partial"
    assert "browser_validation" in report["missing_observations"]
    assert report["browser_evidence"]["source"] == "external-playwright-mcp-or-agent-observation"
    assert report["runs"]["baseline"]["run_id"]


@pytest.mark.asyncio
async def test_model_tier_comparison_reports_compact_stage_changes() -> None:
    client = FakeEquationClient(fail_stage="reverse_conversion", fail_medium_only=True)
    runner = InvestigationRunner(Settings(_env_file=None), diagnostic_client=client)
    report = await runner.investigation_report(
        suite_name="equations-smoke",
        model_tier="heuristic",
        compare_model_tier="medium",
    )
    assert report["comparison"] is not None
    assert report["comparison"]["changed_fixture_count"] > 0
    change = report["comparison"]["changes"][0]
    assert change["baseline_status"] == "passed"
    assert change["candidate_status"] == "failed"
    assert any(item["stage"] == "reverse_conversion" for item in change["stage_changes"])


def test_compare_suite_runs_is_bounded_and_structural() -> None:
    baseline = {
        "run_id": "before",
        "rows": [
            {
                "fixture_id": "a",
                "status": "passed",
                "first_failing_stage": None,
                "stage_matrix": {"burhan_conversion": "pass"},
            }
        ],
    }
    candidate = {
        "run_id": "after",
        "rows": [
            {
                "fixture_id": "a",
                "status": "failed",
                "first_failing_stage": "burhan_conversion",
                "stage_matrix": {"burhan_conversion": "fail"},
            }
        ],
    }
    result = compare_suite_runs(baseline, candidate)
    assert result["baseline_run_id"] == "before"
    assert result["candidate_run_id"] == "after"
    assert result["changes"] == [
        {
            "fixture_id": "a",
            "baseline_status": "passed",
            "candidate_status": "failed",
            "baseline_first_failing_stage": None,
            "candidate_first_failing_stage": "burhan_conversion",
            "stage_changes": [
                {"stage": "burhan_conversion", "baseline": "pass", "candidate": "fail"}
            ],
        }
    ]


@pytest.mark.asyncio
async def test_report_row_limit_and_redaction_are_enforced() -> None:
    client = FakeEquationClient(fail_stage="burhan_conversion", leak_secret=True)
    runner = InvestigationRunner(
        Settings(_env_file=None, dev_mcp_report_max_rows=2),
        diagnostic_client=client,
    )
    result = await runner.run_suite(
        suite_name="equations-adjacency",
        max_fixtures=50,
    )
    assert result["fixture_count"] == 2
    assert result["selection_truncated"] is True
    serialized = repr(result)
    assert "secret-token" not in serialized
    assert "[REDACTED]" in serialized
