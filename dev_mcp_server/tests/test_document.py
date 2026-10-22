from __future__ import annotations

import json

import httpx
import pytest

from albayan_dev_mcp.document import (
    DOCUMENT_DIAGNOSTIC_PATH,
    DOCUMENT_SUITES,
    DocumentDiagnosticClient,
    DocumentMigrationRunner,
    compare_document_reports,
    document_fixtures,
    sanitize_document,
)
from albayan_dev_mcp.investigation import InvestigationRunner, list_suites
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import InMemoryTraceSource


def _settings(**extra):
    return Settings(
        _env_file=None,
        albayan_dev_url="https://dev.example",
        albayan_dev_token="dev-token",
        **extra,
    )


@pytest.mark.asyncio
async def test_document_client_uses_only_fixed_authenticated_endpoint_and_trace():
    events = InMemoryTraceSource()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == DOCUMENT_DIAGNOSTIC_PATH
        assert request.headers["Authorization"] == "Bearer dev-token"
        assert request.headers["X-Trace-Id"] == "test-doc-trace"
        assert json.loads(request.content) == {
            "operation": "normalize",
            "payload": {"document": {"node_type": "DocumentObject", "blocks": []}},
        }
        return httpx.Response(
            200,
            headers={"X-Trace-Id": "test-doc-trace"},
            json={
                "ok": True,
                "status": "passed",
                "operation": "normalize",
                "data": {"node_type": "DocumentObject", "blocks": []},
            },
        )

    client = DocumentDiagnosticClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        trace_source=events,
    )
    report = await client.inspect(
        operation="normalize",
        payload={"document": {"node_type": "DocumentObject", "blocks": []}},
        trace_id="test-doc-trace",
    )
    assert report["status"] == "passed"
    assert report["correlation_preserved"] is True
    assert [e.status for e in events.get_trace("test-doc-trace")] == ["started", "passed"]


@pytest.mark.asyncio
async def test_missing_token_is_blocked_without_network():
    client = DocumentDiagnosticClient(
        Settings(_env_file=None, albayan_dev_url="https://dev.example")
    )
    report = await client.inspect(operation="normalize", payload={})
    assert report["status"] == "blocked"
    assert "ALBAYAN_DEV_TOKEN" in report["missing"]


@pytest.mark.asyncio
async def test_unlisted_operation_and_oversized_payload_rejected_before_network():
    client = DocumentDiagnosticClient(_settings())
    unexpected = await client.inspect(operation="delete_all_articles", payload={})
    assert unexpected["reason"] == "unknown_operation"
    oversized = await client.inspect(operation="normalize", payload={"x": "a" * 132_000})
    assert oversized["reason"] == "fixture_too_large"


@pytest.mark.asyncio
async def test_non_200_diagnostic_does_not_claim_success():
    async def handler(request):
        return httpx.Response(404, json={"detail": "not found"})

    client = DocumentDiagnosticClient(_settings(), transport=httpx.MockTransport(handler))
    report = await client.inspect(operation="normalize", payload={})
    assert report["status"] == "blocked"
    assert report["status_code"] == 404


def test_fixture_registry_is_bounded_and_complete_for_round_one():
    fixtures = document_fixtures()
    ids = {f["id"] for f in fixtures}
    assert len(ids) == len(fixtures)
    assert len(fixtures) >= 12
    assert {"empty-normalize", "paragraph-insert", "invalid-command-id"} <= ids
    assert set(DOCUMENT_SUITES) <= {s["name"] for s in list_suites()}


def test_exact_comparison_reports_behavior_differences_and_rejects_unverified_results():
    baseline = {
        "status": "passed", "operation": "normalize",
        "data": {"node_type": "DocumentObject", "blocks": []},
    }
    same = compare_document_reports(baseline, baseline)
    assert same["equivalent"] is True
    changed = compare_document_reports(
        baseline,
        {
            "status": "passed", "operation": "normalize",
            "data": {"node_type": "DocumentObject", "blocks": [{"value": "lost?"}]},
        },
    )
    assert changed["equivalent"] is False
    assert changed["differences"]
    assert compare_document_reports(baseline, {"status": "blocked"})["status"] == "blocked"


class FakeDocumentClient:
    async def inspect(self, *, operation, payload, trace_id=None):
        if operation == "normalize" and payload.get("document", {}).get("node_type") == "InvalidDocument":
            return {
                "status": "failed", "ok": False, "operation": operation,
                "status_code": 422, "trace_id": "fixture-err",
            }
        if operation == "normalize" and "document" not in payload:
            return {
                "status": "failed", "ok": False, "operation": operation,
                "status_code": 422, "trace_id": "fixture-missing",
            }
        if operation == "normalize":
            return {
                "status": "passed", "ok": True, "operation": operation,
                "data": payload["document"], "trace_id": "fixture-ok",
            }
        return {"status": "blocked", "reason": "not_mocked", "operation": operation}


@pytest.mark.asyncio
async def test_document_suite_checks_expected_negative_cases_not_only_http_200():
    runner = DocumentMigrationRunner(_settings(), client=FakeDocumentClient())
    normal = await runner.run_suite("document-normalization")
    errors = await runner.run_suite("document-error-contracts")
    assert normal["status"] == "passed"
    assert errors["status"] == "passed"
    assert await runner.run_suite("document-final-stress") == {
        "status": "blocked", "blocked": True, "suite": "document-final-stress",
        "reason": "round_7_only",
        "human_actions": ["Run the frozen 145-ID and v1 stress protocol only after full migration."],
    }


@pytest.mark.asyncio
async def test_existing_investigation_registry_dispatches_document_suites(monkeypatch):
    async def fake_run(self, suite_name, *, max_fixtures=50):
        return {"status": "passed", "suite": suite_name, "fixture_count": 1}

    monkeypatch.setattr(DocumentMigrationRunner, "run_suite", fake_run)
    result = await InvestigationRunner(_settings()).run_suite(
        suite_name="document-normalization", max_fixtures=2,
    )
    assert result["status"] == "passed"
    assert result["suite"] == "document-normalization"
    blocked = await InvestigationRunner(_settings()).investigation_report(
        suite_name="document-normalization", compare_model_tier="medium",
    )
    assert blocked["regression_status"] == "blocked"
    assert blocked["reason"] == "model_tier_comparison_not_a_build_comparison"


def test_document_redaction_keeps_real_token_structure_but_hides_credentials():
    content = {
        "tokens": [{"token_id": "inline_1", "math_object": {"node_type": "MathObject"}}],
        "api_key": "private",
        "access_token": "private",
        "token": "private",
        "message": "Bearer simulated-secret",
    }
    cleaned = sanitize_document(content)
    assert cleaned["tokens"][0]["token_id"] == "inline_1"
    assert cleaned["tokens"][0]["math_object"]["node_type"] == "MathObject"
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["access_token"] == "[REDACTED]"
    assert cleaned["token"] == "[REDACTED]"
    assert "simulated-secret" not in cleaned["message"]


def test_comparison_detects_changes_inside_structural_token_lists():
    baseline = {
        "status": "passed",
        "operation": "normalize",
        "data": {"tokens": [{"token_id": "t-1", "text": "أ"}]},
    }
    candidate = {
        "status": "passed",
        "operation": "normalize",
        "data": {"tokens": [{"token_id": "t-1", "text": "ب"}]},
    }
    difference = compare_document_reports(baseline, candidate)
    assert difference["status"] == "failed"
    assert difference["equivalent"] is False
    assert any("tokens[0].text" in row["path"] for row in difference["differences"])
