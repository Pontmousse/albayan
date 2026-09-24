from __future__ import annotations

import json
from importlib.resources import files
from time import perf_counter
from typing import Any

import httpx

from albayan_dev_mcp.sanitize import sanitize
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TRACE_HEADER, TraceSource, resolve_trace_id

DIAGNOSTIC_PATH = "/api/v1/dev/diagnostics/equation"
MODEL_TIERS = ("heuristic", "cheap", "medium")
_STAGE_NAMES = (
    "canonical_input",
    "burhan_conversion",
    "albayan_projection",
    "document2_command",
    "headless_butex_validation",
    "reverse_conversion",
    "browser_validation",
)


class EquationDiagnosticClient:
    """Constrained POST client for the single Al-Bayan equation diagnostic endpoint."""

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

    def _record(
        self,
        *,
        trace_id: str,
        status: str,
        duration_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if self.trace_source is None:
            return
        self.trace_source.record(
            trace_id=trace_id,
            service="dev_mcp",
            stage="equation.inspect",
            status=status,
            duration_ms=duration_ms,
            details=details,
        )

    async def inspect(
        self,
        *,
        latex: str,
        display: bool,
        model_tier: str,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_trace_id = resolve_trace_id(trace_id)
        started = perf_counter()
        self._record(
            trace_id=resolved_trace_id,
            status="started",
            details={"model_tier": model_tier, "display": display},
        )

        config = self.settings.service("albayan")
        missing: list[str] = []
        if not config.configured:
            missing.append(config.url_env)
        if not config.token:
            missing.append(config.token_env)
        if missing:
            self._record(
                trace_id=resolved_trace_id,
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={"reason": "missing_configuration", "missing": missing},
            )
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "reason": "missing_configuration",
                "missing": missing,
                "human_action": (
                    "Configure ALBAYAN_DEV_URL and an authenticated ALBAYAN_DEV_TOKEN. "
                    "The backend diagnostic route also requires DEV_MODE=true."
                ),
            }

        if model_tier not in MODEL_TIERS:
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "reason": "unsupported_model_tier",
                "human_action": "Use heuristic, cheap, or medium for Phase 3 equation diagnostics.",
            }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.token}",
            TRACE_HEADER: resolved_trace_id,
        }
        payload = {
            "latex": latex,
            "display": display,
            "model_tier": model_tier,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.dev_mcp_equation_timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                async with client.stream(
                    "POST",
                    f"{config.url}{DIAGNOSTIC_PATH}",
                    headers=headers,
                    json=payload,
                ) as response:
                    raw, truncated = await _read_bounded(
                        response,
                        max_bytes=self.settings.dev_mcp_max_response_bytes,
                    )
                    body = _decode_json(raw)
                    duration_ms = (perf_counter() - started) * 1000
                    downstream_trace = response.headers.get(TRACE_HEADER)
                    preserved = (
                        downstream_trace == resolved_trace_id
                        if downstream_trace is not None
                        else None
                    )
                    if response.status_code != 200:
                        reason = "diagnostic_request_failed"
                        action = "Inspect the Al-Bayan feature deployment and authentication."
                        if response.status_code == 404:
                            reason = "diagnostic_endpoint_unavailable"
                            action = (
                                "Deploy the Phase 3 Al-Bayan feature branch with DEV_MODE=true; "
                                "the diagnostic route intentionally returns 404 otherwise."
                            )
                        elif response.status_code in {401, 403}:
                            reason = "diagnostic_auth_failed"
                            action = "Provide a valid authenticated ALBAYAN_DEV_TOKEN for the feature deployment."
                        self._record(
                            trace_id=resolved_trace_id,
                            status="blocked",
                            duration_ms=duration_ms,
                            details={"status_code": response.status_code, "reason": reason},
                        )
                        return {
                            "ok": False,
                            "blocked": True,
                            "trace_id": resolved_trace_id,
                            "correlation_preserved": preserved,
                            "reason": reason,
                            "status_code": response.status_code,
                            "response": sanitize(body),
                            "truncated": truncated,
                            "human_action": action,
                        }

                    if not isinstance(body, dict):
                        self._record(
                            trace_id=resolved_trace_id,
                            status="error",
                            duration_ms=duration_ms,
                            details={"reason": "invalid_diagnostic_response"},
                        )
                        return {
                            "ok": False,
                            "blocked": True,
                            "trace_id": resolved_trace_id,
                            "reason": "invalid_diagnostic_response",
                            "human_action": "Inspect the deployed Al-Bayan backend diagnostic endpoint.",
                        }

                    body = sanitize(body)
                    body["trace_id"] = body.get("trace_id") or resolved_trace_id
                    body["correlation_preserved"] = preserved
                    body["truncated"] = truncated
                    self._record(
                        trace_id=resolved_trace_id,
                        status="ok" if body.get("ok") else "partial",
                        duration_ms=duration_ms,
                        details={
                            "model_tier": model_tier,
                            "correlation_preserved": preserved,
                            "partial": body.get("partial"),
                        },
                    )
                    return body
        except httpx.TimeoutException:
            self._record(
                trace_id=resolved_trace_id,
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={"reason": "timeout", "model_tier": model_tier},
            )
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "reason": "timeout",
                "human_action": (
                    "Check the feature deployment and Burhan tier latency, or increase "
                    "DEV_MCP_EQUATION_TIMEOUT_SECONDS within the bounded limit."
                ),
            }
        except httpx.RequestError as exc:
            self._record(
                trace_id=resolved_trace_id,
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={"reason": "service_unreachable", "error_type": type(exc).__name__},
            )
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "reason": "service_unreachable",
                "error_type": type(exc).__name__,
                "human_action": "Check ALBAYAN_DEV_URL and feature-deployment network access.",
            }


async def _read_bounded(response: httpx.Response, *, max_bytes: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    total = 0
    truncated = False
    async for chunk in response.aiter_bytes():
        if total + len(chunk) > max_bytes:
            remaining = max_bytes - total
            if remaining > 0:
                chunks.append(chunk[:remaining])
            truncated = True
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks), truncated


def _decode_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return raw.decode("utf-8", errors="replace")[:20_000]


def load_equation_fixtures() -> list[dict[str, Any]]:
    resource = files("albayan_dev_mcp.fixtures").joinpath("equations.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    fixtures = payload.get("fixtures") if isinstance(payload, dict) else None
    if not isinstance(fixtures, list):
        raise RuntimeError("Equation fixture corpus is malformed")

    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise RuntimeError("Equation fixture must be an object")
        fixture_id = fixture.get("id")
        source = fixture.get("source")
        display = fixture.get("display")
        tags = fixture.get("tags")
        support_class = fixture.get("support_class")
        if (
            not isinstance(fixture_id, str)
            or not fixture_id
            or fixture_id in seen
            or not isinstance(source, str)
            or not source
            or not isinstance(display, bool)
            or not isinstance(tags, list)
            or not all(isinstance(tag, str) and tag for tag in tags)
            or not isinstance(support_class, str)
            or not support_class
        ):
            raise RuntimeError(f"Invalid equation fixture: {fixture_id!r}")
        known_failure = fixture.get("known_failure")
        if known_failure is not None and not isinstance(known_failure, str):
            raise RuntimeError(f"Invalid known_failure for equation fixture {fixture_id}")
        seen.add(fixture_id)
        validated.append(dict(fixture))
    return validated


def fixture_by_id(fixture_id: str) -> dict[str, Any] | None:
    for fixture in load_equation_fixtures():
        if fixture["id"] == fixture_id:
            return fixture
    return None


def stage_matrix(report: dict[str, Any]) -> dict[str, str]:
    stages = report.get("stages")
    if not isinstance(stages, dict):
        return {name: "unavailable" for name in _STAGE_NAMES}
    matrix: dict[str, str] = {}
    for name in _STAGE_NAMES:
        stage = stages.get(name)
        if not isinstance(stage, dict) or stage.get("available") is False:
            matrix[name] = "unavailable"
        elif stage.get("ok") is True:
            matrix[name] = "pass"
        elif stage.get("ok") is False:
            matrix[name] = "fail"
        else:
            matrix[name] = "unknown"
    return matrix


def compare_reports(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = reports.get("heuristic")
    comparison: dict[str, Any] = {
        "baseline": "heuristic",
        "tiers": {},
    }
    baseline_signature = _comparison_signature(baseline) if isinstance(baseline, dict) else None
    for tier in MODEL_TIERS:
        report = reports.get(tier, {})
        signature = _comparison_signature(report)
        comparison["tiers"][tier] = {
            "ok": report.get("ok"),
            "blocked": report.get("blocked", False),
            "trace_id": report.get("trace_id"),
            "stage_matrix": stage_matrix(report),
            "mappings": signature.get("mappings") if signature else None,
            "warnings": signature.get("warnings") if signature else None,
            "reverse_latex": signature.get("reverse_latex") if signature else None,
            "burhan_duration_ms": signature.get("burhan_duration_ms") if signature else None,
            "headless_butex": signature.get("headless_butex") if signature else None,
            "differences_from_heuristic": (
                []
                if tier == "heuristic" or baseline_signature is None or signature is None
                else json_diff(baseline_signature, signature, limit=100)
            ),
        }
    return comparison


def _comparison_signature(report: dict[str, Any]) -> dict[str, Any] | None:
    stages = report.get("stages")
    if not isinstance(stages, dict):
        return None

    def data(name: str) -> dict[str, Any]:
        stage = stages.get(name)
        raw = stage.get("data") if isinstance(stage, dict) else None
        return raw if isinstance(raw, dict) else {}

    burhan = data("burhan_conversion")
    projection = data("albayan_projection")
    reverse = data("reverse_conversion")
    headless = data("headless_butex_validation")
    return {
        "english_json": burhan.get("english_json"),
        "arabic_json": burhan.get("arabic_json"),
        "mappings": burhan.get("mappings"),
        "warnings": burhan.get("warnings"),
        "editor_math_object": projection.get("editor_math_object"),
        "reverse_latex": reverse.get("canonical_latex"),
        "burhan_duration_ms": burhan.get("duration_ms"),
        "headless_butex": {
            key: headless.get(key)
            for key in ("ok", "stage", "editable", "english_latex", "arabic_latex", "error")
            if key in headless
        },
    }


def json_diff(left: Any, right: Any, *, path: str = "$", limit: int = 100) -> list[dict[str, Any]]:
    """Return a bounded structural JSON diff; this is not an equation parser."""
    differences: list[dict[str, Any]] = []

    def walk(a: Any, b: Any, current: str) -> None:
        if len(differences) >= limit:
            return
        if type(a) is not type(b):
            differences.append({"path": current, "left": a, "right": b})
            return
        if isinstance(a, dict):
            for key in sorted(set(a) | set(b)):
                if len(differences) >= limit:
                    return
                child = f"{current}.{key}"
                if key not in a:
                    differences.append({"path": child, "left": None, "right": b[key]})
                elif key not in b:
                    differences.append({"path": child, "left": a[key], "right": None})
                else:
                    walk(a[key], b[key], child)
            return
        if isinstance(a, list):
            if len(a) != len(b):
                differences.append({"path": f"{current}.length", "left": len(a), "right": len(b)})
            for index, (a_item, b_item) in enumerate(zip(a, b, strict=False)):
                walk(a_item, b_item, f"{current}[{index}]")
                if len(differences) >= limit:
                    return
            return
        if a != b:
            differences.append({"path": current, "left": a, "right": b})

    walk(left, right, path)
    return differences[:limit]
