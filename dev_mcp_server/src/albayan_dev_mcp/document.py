from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from importlib.resources import files
from time import perf_counter
from typing import Any
from uuid import uuid4

import httpx

from albayan_dev_mcp.equation import json_diff
from albayan_dev_mcp.sanitize import sanitize
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TRACE_HEADER, TraceSource, resolve_trace_id

DOCUMENT_DIAGNOSTIC_PATH = "/api/v1/dev/diagnostics/document"
DOCUMENT_OPERATIONS = (
    "diagnose_contract", "normalize", "outline", "references",
    "reference_index", "export", "diff", "apply_command",
    "diagnose_math_object", "project_math_object_english",
)
DOCUMENT_SUITES = {
    "document-contract-smoke": "worker-contract",
    "document-normalization": "normalization",
    "document-commands": "commands",
    "document-references": "references",
    "document-math-roundtrip": "math",
    "document-export": "export",
    "document-error-contracts": "errors",
    "document-final-stress": "stress",
}


def canonical_hash(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def document_fixtures() -> list[dict[str, Any]]:
    resource = files("albayan_dev_mcp.fixtures").joinpath("documents.json")
    raw = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1 or not isinstance(raw.get("fixtures"), list):
        raise RuntimeError("Document diagnostic fixture corpus is invalid")
    seen: set[str] = set()
    for fixture in raw["fixtures"]:
        if not isinstance(fixture, dict):
            raise RuntimeError("Invalid document fixture")
        fixture_id = fixture.get("id")
        if (
            not isinstance(fixture_id, str) or not fixture_id or fixture_id in seen
            or fixture.get("suite") not in DOCUMENT_SUITES
            or fixture.get("operation") not in DOCUMENT_OPERATIONS
            or not isinstance(fixture.get("payload"), dict)
            or fixture.get("expect_status") not in {"passed", "failed"}
        ):
            raise RuntimeError(f"Invalid document fixture {fixture_id!r}")
        seen.add(fixture_id)
    return raw["fixtures"]


class DocumentDiagnosticClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        trace_source: TraceSource | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.trace_source = trace_source

    async def inspect(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        resolved = resolve_trace_id(trace_id)
        if operation not in DOCUMENT_OPERATIONS:
            return {
                "ok": False, "status": "blocked", "blocked": True,
                "trace_id": resolved, "reason": "unknown_operation",
                "human_action": "Choose a supported stateless document diagnostic operation.",
            }
        serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(serialized) > 131_072:
            return {
                "ok": False, "status": "blocked", "blocked": True,
                "trace_id": resolved, "reason": "fixture_too_large",
                "human_action": "Use a bounded synthetic fixture no larger than 128 KiB.",
            }
        config = self.settings.service("albayan")
        if not config.configured or not config.token:
            return {
                "ok": False, "status": "blocked", "blocked": True,
                "trace_id": resolved, "reason": "missing_configuration",
                "missing": [
                    name for name, available in (
                        (config.url_env, config.configured),
                        (config.token_env, bool(config.token)),
                    ) if not available
                ],
                "human_action": "Configure an authenticated development Al-Bayan diagnostic origin/token and DEV_MODE=true.",
            }
        started = perf_counter()
        if self.trace_source:
            self.trace_source.record(
                trace_id=resolved, service="dev_mcp", stage="document.inspect",
                status="started", details={"operation": operation},
            )
        try:
            async with httpx.AsyncClient(
                transport=self.transport, follow_redirects=False,
                timeout=self.settings.dev_mcp_request_timeout_seconds,
            ) as client:
                async with client.stream(
                    "POST",
                    f"{config.url}{DOCUMENT_DIAGNOSTIC_PATH}",
                    headers={
                        "Authorization": f"Bearer {config.token}",
                        "Accept": "application/json",
                        TRACE_HEADER: resolved,
                    },
                    json={"operation": operation, "payload": payload},
                ) as response:
                    limit = self.settings.dev_mcp_max_response_bytes
                    content = bytearray()
                    truncated = False
                    async for chunk in response.aiter_bytes():
                        if len(content) + len(chunk) > limit:
                            content.extend(chunk[: max(0, limit - len(content))])
                            truncated = True
                            break
                        content.extend(chunk)
                    try:
                        body = json.loads(content.decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        body = None
                    if response.status_code != 200 or not isinstance(body, dict):
                        result = {
                            "ok": False, "status": "blocked", "blocked": True,
                            "reason": "diagnostic_endpoint_unavailable",
                            "status_code": response.status_code,
                            "human_action": "Check the DEV_MODE-gated Al-Bayan document endpoint and authenticated development deployment.",
                        }
                    elif truncated or body.get("status") not in {"passed", "failed", "blocked"}:
                        result = {
                            "ok": False, "status": "blocked", "blocked": True,
                            "reason": "invalid_or_truncated_diagnostic",
                            "human_action": "Inspect the deployed document diagnostic adapter and response size.",
                        }
                    else:
                        result = sanitize(body)
                    result.update({
                        "trace_id": resolved,
                        "correlation_preserved": (
                            response.headers.get(TRACE_HEADER) == resolved
                            if response.headers.get(TRACE_HEADER) is not None else None
                        ),
                        "operation": operation,
                        "duration_ms": round((perf_counter() - started) * 1000, 3),
                    })
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            result = {
                "ok": False, "status": "blocked", "blocked": True,
                "trace_id": resolved, "operation": operation,
                "reason": "timeout" if isinstance(exc, httpx.TimeoutException) else "service_unreachable",
                "error_type": type(exc).__name__,
                "human_action": "Check the configured development backend deployment and network access.",
            }
        if self.trace_source:
            self.trace_source.record(
                trace_id=resolved, service="dev_mcp", stage="document.inspect",
                status=result["status"],
                duration_ms=(perf_counter() - started) * 1000,
                details={"operation": operation},
            )
        return result


def compare_document_reports(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if (
        baseline.get("status") != "passed" or candidate.get("status") != "passed"
        or baseline.get("operation") != candidate.get("operation")
        or "data" not in baseline or "data" not in candidate
    ):
        return {
            "status": "blocked",
            "equivalent": None,
            "reason": "incompatible_or_unverified_reports",
            "human_action": "Supply two successful reports for the same operation from attested baseline/candidate builds.",
        }
    left, right = baseline["data"], candidate["data"]
    differences = json_diff(left, right, limit=30)
    return sanitize({
        "status": "passed" if not differences else "failed",
        "equivalent": not differences,
        "operation": baseline["operation"],
        "baseline_sha256": canonical_hash(left),
        "candidate_sha256": canonical_hash(right),
        "differences": differences,
        "comparison": "exact_json_semantics_no_ignored_fields",
        "note": "Generated IDs and harmless formatting may require a separately justified semantic comparison; never auto-ignore differences.",
    })


class DocumentMigrationRunner:
    def __init__(self, settings: Settings, *, trace_source: TraceSource | None = None, client: Any = None):
        self.settings = settings
        self.trace_source = trace_source
        self.client = client

    async def run_suite(self, suite_name: str, *, max_fixtures: int = 50) -> dict[str, Any]:
        if suite_name not in DOCUMENT_SUITES:
            return {"status": "blocked", "reason": "unknown_suite", "suite": suite_name}
        if suite_name == "document-final-stress":
            return {
                "status": "blocked", "blocked": True, "suite": suite_name,
                "reason": "round_7_only",
                "human_actions": ["Run the frozen 145-ID and v1 stress protocol only after full migration."],
            }
        fixtures = [f for f in document_fixtures() if f["suite"] == suite_name]
        selected = fixtures[:min(max_fixtures, self.settings.dev_mcp_report_max_rows)]
        client = self.client or DocumentDiagnosticClient(self.settings, trace_source=self.trace_source)
        rows: list[dict[str, Any]] = []
        for fixture in selected:
            report = await client.inspect(
                operation=fixture["operation"],
                payload=fixture["payload"],
            )
            observed = report.get("status", "blocked")
            expected = fixture["expect_status"]
            actual_code = report.get("status_code")
            expected_code = fixture.get("expect_status_code")
            blocked = observed == "blocked"
            passed = (
                observed == expected
                and (expected_code is None or actual_code == expected_code)
            )
            state = "blocked" if blocked else ("passed" if passed else "failed")
            rows.append({
                "fixture_id": fixture["id"],
                "operation": fixture["operation"],
                "fixture_sha256": canonical_hash(fixture["payload"]),
                "expected_status": expected,
                "observed_status": observed,
                "expected_status_code": expected_code,
                "observed_status_code": actual_code,
                "status": state,
                "trace_id": report.get("trace_id"),
                "first_failing_stage": "butex_worker" if state == "failed" else None,
                "stage_matrix": {"butex_worker": "pass" if passed else state},
                "blockers": [{"reason": report.get("reason", "unavailable")}] if blocked else [],
                "missing_observations": ["butex_worker"] if blocked else [],
                "human_actions": [report["human_action"]] if report.get("human_action") else [],
                "data_sha256": canonical_hash(report.get("data")) if report.get("data") is not None else None,
            })
        statuses = [row["status"] for row in rows]
        status = (
            "blocked" if not statuses or all(x == "blocked" for x in statuses)
            else "failed" if "failed" in statuses
            else "partial" if "blocked" in statuses
            else "passed"
        )
        return sanitize({
            "schema_version": 1,
            "run_id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "domain": "document",
            "suite": {"name": suite_name, "domain": "document", "ci_policy": "opt-in-live"},
            "status": status, "ok": status == "passed",
            "blocked": status == "blocked",
            "partial": status == "partial",
            "fixture_count": len(rows),
            "selection_truncated": len(fixtures) > len(rows),
            "trace_ids": [row["trace_id"] for row in rows if row.get("trace_id")],
            "first_failing_stage": "butex_worker" if "failed" in statuses else None,
            "likely_owning_service": "butex" if "failed" in statuses else None,
            "ownership_basis": "First observed diagnostic boundary, not proof of root cause.",
            "blockers": [b for row in rows for b in row["blockers"]],
            "missing_observations": list(dict.fromkeys(
                item for row in rows for item in row["missing_observations"]
            )),
            "human_actions": list(dict.fromkeys(
                item for row in rows for item in row["human_actions"]
            )),
            "rows": rows,
        })
