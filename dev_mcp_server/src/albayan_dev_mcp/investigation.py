from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from albayan_dev_mcp.equation import (
    MODEL_TIERS,
    EquationDiagnosticClient,
    compare_reports,
    load_equation_fixtures,
    stage_matrix,
)
from albayan_dev_mcp.sanitize import sanitize
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TraceSource, resolve_trace_id

REPORT_SCHEMA_VERSION = 1
ModelTier = Literal["heuristic", "cheap", "medium"]
RunStatus = Literal["passed", "failed", "partial", "blocked"]

_OPTIONAL_STAGES = {"browser_validation"}
_STAGE_OWNERS = {
    "canonical_input": "caller",
    "burhan_conversion": "burhan",
    "albayan_projection": "albayan-backend",
    "document2_command": "butex-document2",
    "headless_butex_validation": "butex",
    "reverse_conversion": "burhan",
    "browser_validation": "frontend-browser",
}


@dataclass(frozen=True)
class SuiteSpec:
    name: str
    domain: str
    description: str
    mode: Literal["fixtures", "tier-comparison"]
    fixture_ids: tuple[str, ...] = ()
    tag: str | None = None
    deterministic: bool = True
    live: bool = True
    ci_policy: Literal["offline-contract", "opt-in-live"] = "opt-in-live"
    default_model_tier: ModelTier = "heuristic"

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "mode": self.mode,
            "deterministic": self.deterministic,
            "live": self.live,
            "ci_policy": self.ci_policy,
            "default_model_tier": self.default_model_tier,
        }


_SUITES: dict[str, SuiteSpec] = {
    "equations-smoke": SuiteSpec(
        name="equations-smoke",
        domain="equation",
        description="Small representative equation pipeline smoke suite.",
        mode="fixtures",
        fixture_ids=(
            "basic-add",
            "superscript",
            "fraction",
            "sqrt",
            "theta",
            "sin-theta",
            "sum-indexed",
            "integral-dx",
        ),
        deterministic=True,
        live=True,
        ci_policy="opt-in-live",
    ),
    "equations-adjacency": SuiteSpec(
        name="equations-adjacency",
        domain="equation",
        description="Historically sensitive adjacency and differential-token cases.",
        mode="fixtures",
        tag="adjacency",
        deterministic=True,
        live=True,
        ci_policy="opt-in-live",
    ),
    "equations-common-scientific": SuiteSpec(
        name="equations-common-scientific",
        domain="equation",
        description="Common scientific notation, operators, typography, derivatives and environments.",
        mode="fixtures",
        fixture_ids=(
            "fraction",
            "sqrt",
            "sum-indexed",
            "integral-dx",
            "partial-derivative",
            "mathbf-x",
            "mathbb-expectation",
            "operatorname-var",
            "cases",
            "dot-x",
            "ddot-x",
            "norm-x-2",
        ),
        deterministic=True,
        live=True,
        ci_policy="opt-in-live",
    ),
    "document2-roundtrip": SuiteSpec(
        name="document2-roundtrip",
        domain="equation",
        description="Equation fixtures chosen to exercise Document2 insertion, BuTeX reopen and reverse conversion.",
        mode="fixtures",
        fixture_ids=(
            "basic-add",
            "fraction",
            "text-subject-to",
            "cases",
            "df-over-dx",
        ),
        deterministic=True,
        live=True,
        ci_policy="opt-in-live",
    ),
    "burhan-tier-comparison": SuiteSpec(
        name="burhan-tier-comparison",
        domain="equation",
        description="Compare heuristic, cheap and medium Burhan behavior on a bounded regression subset.",
        mode="tier-comparison",
        fixture_ids=("df-over-dx", "partial-derivative", "text-subject-to"),
        deterministic=False,
        live=True,
        ci_policy="opt-in-live",
    ),
}


def list_suites() -> list[dict[str, Any]]:
    """Return stable suite discovery metadata without touching live services."""

    return [spec.metadata() for spec in _SUITES.values()]


def suite_by_name(name: str) -> SuiteSpec | None:
    return _SUITES.get(name)


def capabilities(settings: Settings) -> dict[str, Any]:
    """Describe configured development capabilities without inventing reachability."""

    services: dict[str, Any] = {}
    human_actions: list[str] = []
    for name in ("albayan", "burhan", "butex"):
        config = settings.service(name)  # type: ignore[arg-type]
        state = "configured" if config.configured else "missing_configuration"
        services[name] = {
            "state": state,
            "url_configured": config.configured,
            "token_configured": bool(config.token),
            "note": "Configuration state only; use dev_health for live reachability.",
        }
        if not config.configured:
            human_actions.append(f"Configure {config.url_env} if investigations require {name} direct access.")

    albayan = settings.service("albayan")
    equation_ready = bool(albayan.configured and albayan.token)
    if not albayan.configured:
        human_actions.append("Configure ALBAYAN_DEV_URL to run live equation regression suites.")
    if not albayan.token:
        human_actions.append("Configure an authenticated ALBAYAN_DEV_TOKEN to run live equation diagnostics.")

    if not settings.dev_mcp_browser_observation_available:
        human_actions.append(
            "Browser observation is not declared available; use/configure the separate Playwright MCP when browser evidence is required."
        )

    return sanitize(
        {
            "schema_version": REPORT_SCHEMA_VERSION,
            "services": services,
            "features": {
                "trace_lookup": True,
                "equation_inspection": equation_ready,
                "named_regression_suites": True,
                "suite_names": list(_SUITES),
                "comparison_support": True,
                "burhan_tiers": list(MODEL_TIERS),
                "butex_editor_import": equation_ready,
                "browser_observation": settings.dev_mcp_browser_observation_available,
                "browser_observation_source": "external-playwright-mcp",
                "offline_contract_ci": True,
                "live_suite_execution": equation_ready,
            },
            "human_actions": _unique(human_actions),
        }
    )


class InvestigationRunner:
    """Bounded orchestration over existing diagnostics; it owns no parser or editor model."""

    def __init__(
        self,
        settings: Settings,
        *,
        trace_source: TraceSource | None = None,
        diagnostic_client: Any | None = None,
    ) -> None:
        self.settings = settings
        self.trace_source = trace_source
        self._diagnostic_client = diagnostic_client

    def _client(self) -> Any:
        if self._diagnostic_client is not None:
            return self._diagnostic_client
        return EquationDiagnosticClient(self.settings, trace_source=self.trace_source)

    async def run_suite(
        self,
        *,
        suite_name: str,
        model_tier: ModelTier = "heuristic",
        max_fixtures: int = 50,
    ) -> dict[str, Any]:
        spec = suite_by_name(suite_name)
        if spec is None:
            return {
                "schema_version": REPORT_SCHEMA_VERSION,
                "ok": False,
                "blocked": True,
                "status": "blocked",
                "reason": "suite_not_found",
                "suite": suite_name,
                "available_suites": list(_SUITES),
                "human_actions": ["Choose one of the suite names returned by dev_regression_suites."],
            }
        if model_tier not in MODEL_TIERS:
            return {
                "schema_version": REPORT_SCHEMA_VERSION,
                "ok": False,
                "blocked": True,
                "status": "blocked",
                "reason": "unsupported_model_tier",
                "suite": suite_name,
                "human_actions": ["Use heuristic, cheap, or medium."],
            }

        started_at = datetime.now(UTC)
        started = perf_counter()
        run_id = str(uuid4())
        fixtures = _select_fixtures(spec)
        hard_limit = min(max_fixtures, self.settings.dev_mcp_report_max_rows)
        selected = fixtures[:hard_limit]
        truncated = len(fixtures) > len(selected)

        if spec.mode == "tier-comparison":
            rows = await self._run_tier_comparison_rows(selected)
        else:
            rows = await self._run_fixture_rows(selected, model_tier=model_tier)

        summary = _summarize_rows(rows)
        completed_at = datetime.now(UTC)
        payload = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "run_id": run_id,
            "domain": spec.domain,
            "suite": spec.metadata(),
            "model_tier": model_tier if spec.mode == "fixtures" else None,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_ms": round((perf_counter() - started) * 1000, 3),
            "status": summary["status"],
            "ok": summary["status"] == "passed",
            "blocked": summary["status"] == "blocked",
            "partial": summary["status"] == "partial",
            "fixture_count": len(rows),
            "selection_truncated": truncated,
            "trace_ids": summary["trace_ids"],
            "first_failing_stage": summary["first_failing_stage"],
            "likely_owning_service": summary["likely_owning_service"],
            "ownership_basis": summary["ownership_basis"],
            "blockers": summary["blockers"],
            "missing_observations": summary["missing_observations"],
            "human_actions": summary["human_actions"],
            "rows": rows,
        }
        return sanitize(payload)

    async def investigation_report(
        self,
        *,
        suite_name: str,
        model_tier: ModelTier = "heuristic",
        compare_model_tier: ModelTier | None = None,
        require_browser: bool = False,
        browser_observation: Literal["not_checked", "passed", "failed", "blocked"] = "not_checked",
        browser_note: str | None = None,
    ) -> dict[str, Any]:
        investigation_id = str(uuid4())
        baseline = await self.run_suite(
            suite_name=suite_name,
            model_tier=model_tier,
        )
        candidate: dict[str, Any] | None = None
        comparison: dict[str, Any] | None = None
        if compare_model_tier is not None and compare_model_tier != model_tier:
            candidate = await self.run_suite(
                suite_name=suite_name,
                model_tier=compare_model_tier,
            )
            comparison = compare_suite_runs(baseline, candidate)

        status = str(baseline.get("status", "blocked"))
        problem_reproduced: bool | None
        if status == "failed":
            problem_reproduced = True
        elif status == "passed":
            problem_reproduced = False
        else:
            problem_reproduced = None

        missing = list(baseline.get("missing_observations") or [])
        blockers = list(baseline.get("blockers") or [])
        human_actions = list(baseline.get("human_actions") or [])
        if candidate:
            missing.extend(candidate.get("missing_observations") or [])
            blockers.extend(candidate.get("blockers") or [])
            human_actions.extend(candidate.get("human_actions") or [])

        browser = {
            "source": "external-playwright-mcp-or-agent-observation",
            "required": require_browser,
            "observation": browser_observation,
            "note": browser_note,
        }
        if require_browser and browser_observation == "not_checked":
            missing.append("browser_validation")
            human_actions.append(
                "Use the separate Playwright MCP and supply browser-observed evidence before drawing a browser-dependent conclusion."
            )
            if status == "passed":
                status = "partial"
        if browser_observation == "failed" and status == "passed":
            status = "failed"
            problem_reproduced = True

        evidence = _build_evidence_summary(baseline, candidate, browser)
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "investigation_id": investigation_id,
            "domain": baseline.get("domain", "equation"),
            "suite": suite_name,
            "problem_reproduced": problem_reproduced,
            "configuration": {
                "baseline_model_tier": model_tier,
                "candidate_model_tier": compare_model_tier,
            },
            "trace_ids": _unique(
                list(baseline.get("trace_ids") or [])
                + (list(candidate.get("trace_ids") or []) if candidate else [])
            ),
            "first_failing_stage": baseline.get("first_failing_stage"),
            "likely_owning_service": baseline.get("likely_owning_service"),
            "ownership_basis": baseline.get("ownership_basis"),
            "regression_status": status,
            "observed_evidence": evidence,
            "comparison": comparison,
            "browser_evidence": browser,
            "missing_observations": _unique(missing),
            "blockers": _dedupe_dicts(blockers),
            "human_actions": _unique(human_actions),
            "runs": {
                "baseline": _compact_run(baseline),
                "candidate": _compact_run(candidate) if candidate else None,
            },
        }
        return sanitize(report)

    async def _run_fixture_rows(
        self,
        fixtures: list[dict[str, Any]],
        *,
        model_tier: ModelTier,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        client = self._client()
        for fixture in fixtures:
            trace_id = resolve_trace_id(None)
            report = await client.inspect(
                latex=fixture["source"],
                display=fixture["display"],
                model_tier=model_tier,
                trace_id=trace_id,
            )
            rows.append(_row_from_report(fixture, report))
        return rows

    async def _run_tier_comparison_rows(
        self,
        fixtures: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        client = self._client()
        for fixture in fixtures:
            trace_id = resolve_trace_id(None)
            reports: dict[str, dict[str, Any]] = {}
            for tier in MODEL_TIERS:
                reports[tier] = await client.inspect(
                    latex=fixture["source"],
                    display=fixture["display"],
                    model_tier=tier,
                    trace_id=trace_id,
                )
            tier_rows = {tier: _row_from_report(fixture, report) for tier, report in reports.items()}
            statuses = [row["status"] for row in tier_rows.values()]
            status: RunStatus = "passed"
            if all(value == "blocked" for value in statuses):
                status = "blocked"
            elif "failed" in statuses:
                status = "failed"
            elif "blocked" in statuses or "partial" in statuses:
                status = "partial"
            failed_stage = next(
                (row["first_failing_stage"] for row in tier_rows.values() if row["first_failing_stage"]),
                None,
            )
            rows.append(
                {
                    "fixture_id": fixture["id"],
                    "source": fixture["source"],
                    "trace_id": trace_id,
                    "status": status,
                    "first_failing_stage": failed_stage,
                    "likely_owning_service": likely_owner(failed_stage),
                    "tier_status": {
                        tier: {
                            "status": row["status"],
                            "first_failing_stage": row["first_failing_stage"],
                            "stage_matrix": row["stage_matrix"],
                        }
                        for tier, row in tier_rows.items()
                    },
                    "comparison": compare_reports(reports),
                    "blockers": _dedupe_dicts(
                        [blocker for row in tier_rows.values() for blocker in row["blockers"]]
                    ),
                    "missing_observations": _unique(
                        [item for row in tier_rows.values() for item in row["missing_observations"]]
                    ),
                    "human_actions": _unique(
                        [item for row in tier_rows.values() for item in row["human_actions"]]
                    ),
                }
            )
        return rows


def compare_suite_runs(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compact bounded comparison of two already-observed suite runs."""

    left_rows = {
        str(row.get("fixture_id")): row
        for row in baseline.get("rows", [])
        if isinstance(row, dict) and row.get("fixture_id")
    }
    right_rows = {
        str(row.get("fixture_id")): row
        for row in candidate.get("rows", [])
        if isinstance(row, dict) and row.get("fixture_id")
    }
    changes: list[dict[str, Any]] = []
    limit = 50
    for fixture_id in sorted(set(left_rows) | set(right_rows)):
        left = left_rows.get(fixture_id)
        right = right_rows.get(fixture_id)
        if left is None or right is None:
            changes.append(
                {
                    "fixture_id": fixture_id,
                    "change": "added" if left is None else "removed",
                }
            )
        else:
            stage_changes = _stage_changes(left.get("stage_matrix"), right.get("stage_matrix"))
            if left.get("status") != right.get("status") or stage_changes:
                changes.append(
                    {
                        "fixture_id": fixture_id,
                        "baseline_status": left.get("status"),
                        "candidate_status": right.get("status"),
                        "baseline_first_failing_stage": left.get("first_failing_stage"),
                        "candidate_first_failing_stage": right.get("first_failing_stage"),
                        "stage_changes": stage_changes,
                    }
                )
        if len(changes) >= limit:
            break
    return {
        "baseline_run_id": baseline.get("run_id"),
        "candidate_run_id": candidate.get("run_id"),
        "changed_fixture_count": len(changes),
        "truncated": len(changes) >= limit,
        "changes": changes,
    }


def likely_owner(stage: str | None) -> str | None:
    return _STAGE_OWNERS.get(stage) if stage else None


def _select_fixtures(spec: SuiteSpec) -> list[dict[str, Any]]:
    fixtures = load_equation_fixtures()
    if spec.fixture_ids:
        by_id = {fixture["id"]: fixture for fixture in fixtures}
        return [by_id[fixture_id] for fixture_id in spec.fixture_ids if fixture_id in by_id]
    if spec.tag:
        return [fixture for fixture in fixtures if spec.tag in fixture["tags"]]
    return fixtures


def _row_from_report(fixture: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    matrix = stage_matrix(report)
    failed_stages = [name for name, state in matrix.items() if state == "fail"]
    unavailable = [
        name
        for name, state in matrix.items()
        if state == "unavailable" and name not in _OPTIONAL_STAGES
    ]
    first_failing_stage = failed_stages[0] if failed_stages else None
    if report.get("blocked"):
        status: RunStatus = "blocked"
    elif failed_stages:
        status = "failed"
    elif unavailable:
        status = "partial"
    else:
        status = "passed"

    blockers = _extract_blockers(report)
    actions = _extract_human_actions(report)
    return {
        "fixture_id": fixture["id"],
        "source": fixture["source"],
        "display": fixture["display"],
        "support_class": fixture.get("support_class"),
        "known_failure": fixture.get("known_failure"),
        "trace_id": report.get("trace_id"),
        "status": status,
        "first_failing_stage": first_failing_stage,
        "likely_owning_service": likely_owner(first_failing_stage),
        "ownership_basis": (
            f"First observable failing boundary: {first_failing_stage}"
            if first_failing_stage
            else None
        ),
        "stage_matrix": matrix,
        "blockers": blockers,
        "missing_observations": unavailable,
        "optional_missing_observations": [
            name for name, state in matrix.items() if state == "unavailable" and name in _OPTIONAL_STAGES
        ],
        "human_actions": actions,
        "evidence": _failure_evidence(report),
    }


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [row.get("status") for row in rows]
    if not rows or all(status == "blocked" for status in statuses):
        status: RunStatus = "blocked"
    elif "failed" in statuses:
        status = "failed"
    elif "blocked" in statuses or "partial" in statuses:
        status = "partial"
    else:
        status = "passed"

    first_failing_stage = next(
        (row.get("first_failing_stage") for row in rows if row.get("first_failing_stage")),
        None,
    )
    owner = likely_owner(first_failing_stage)
    return {
        "status": status,
        "trace_ids": _unique([row.get("trace_id") for row in rows if row.get("trace_id")]),
        "first_failing_stage": first_failing_stage,
        "likely_owning_service": owner,
        "ownership_basis": (
            f"Derived from the first observable failing stage ({first_failing_stage}); not proof of root cause."
            if owner
            else "No observable failing stage was available to assign ownership."
        ),
        "blockers": _dedupe_dicts([item for row in rows for item in row.get("blockers", [])]),
        "missing_observations": _unique(
            [item for row in rows for item in row.get("missing_observations", [])]
        ),
        "human_actions": _unique([item for row in rows for item in row.get("human_actions", [])]),
    }


def _extract_blockers(report: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if report.get("blocked"):
        blockers.append(
            {
                "reason": report.get("reason", "blocked"),
                "status_code": report.get("status_code"),
            }
        )
    stages = report.get("stages")
    if isinstance(stages, dict):
        for name, stage in stages.items():
            if not isinstance(stage, dict):
                continue
            if stage.get("blocked") or stage.get("available") is False:
                blockers.append(
                    {
                        "stage": name,
                        "reason": stage.get("reason") or stage.get("error") or "unavailable",
                    }
                )
    return _dedupe_dicts(blockers)


def _extract_human_actions(report: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    action = report.get("human_action")
    if isinstance(action, str) and action:
        actions.append(action)
    raw_actions = report.get("human_actions")
    if isinstance(raw_actions, list):
        actions.extend(item for item in raw_actions if isinstance(item, str) and item)
    stages = report.get("stages")
    if isinstance(stages, dict):
        for stage in stages.values():
            if isinstance(stage, dict):
                value = stage.get("human_action")
                if isinstance(value, str) and value:
                    actions.append(value)
    return _unique(actions)


def _failure_evidence(report: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    stages = report.get("stages")
    if not isinstance(stages, dict):
        return evidence
    for name, stage in stages.items():
        if not isinstance(stage, dict):
            continue
        if stage.get("ok") is False or stage.get("available") is False or stage.get("blocked"):
            evidence.append(
                {
                    "stage": name,
                    "available": stage.get("available"),
                    "ok": stage.get("ok"),
                    "reason": stage.get("reason"),
                    "error": stage.get("error"),
                }
            )
        if len(evidence) >= 12:
            break
    return evidence


def _build_evidence_summary(
    baseline: dict[str, Any],
    candidate: dict[str, Any] | None,
    browser: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for label, run in (("baseline", baseline), ("candidate", candidate)):
        if not run:
            continue
        evidence.append(
            {
                "source": "deterministic-headless-dev-mcp",
                "configuration": label,
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "first_failing_stage": run.get("first_failing_stage"),
                "likely_owning_service": run.get("likely_owning_service"),
                "trace_ids": list(run.get("trace_ids") or [])[:20],
            }
        )
    if browser.get("observation") != "not_checked":
        evidence.append(
            {
                "source": "browser-observation-external",
                "status": browser.get("observation"),
                "note": browser.get("note"),
            }
        )
    return evidence


def _compact_run(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "fixture_count": run.get("fixture_count"),
        "selection_truncated": run.get("selection_truncated"),
        "trace_ids": list(run.get("trace_ids") or [])[:20],
        "first_failing_stage": run.get("first_failing_stage"),
        "likely_owning_service": run.get("likely_owning_service"),
        "missing_observations": list(run.get("missing_observations") or [])[:20],
        "blocker_count": len(run.get("blockers") or []),
    }


def _stage_changes(left: Any, right: Any) -> list[dict[str, Any]]:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return []
    changes: list[dict[str, Any]] = []
    for stage in sorted(set(left) | set(right)):
        if left.get(stage) != right.get(stage):
            changes.append(
                {
                    "stage": stage,
                    "baseline": left.get(stage),
                    "candidate": right.get(stage),
                }
            )
    return changes


def _unique(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _dedupe_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _unique(values)
