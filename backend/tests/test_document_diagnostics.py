from __future__ import annotations

from fastapi import HTTPException
from pydantic import ValidationError

from app.routers import dev_diagnostics
from app.schemas.dev_diagnostics import DocumentDiagnosticRequest
from app.services import document_diagnostic_service


def test_diagnostic_normalize_uses_actual_worker_client(monkeypatch):
    source = {"node_type": "DocumentObject", "blocks": []}
    observed = []

    def fake_normalize(document):
        observed.append(document)
        return {"node_type": "DocumentObject", "blocks": [], "meta": {}}

    monkeypatch.setattr(
        document_diagnostic_service.butex_worker_client, "normalize_document", fake_normalize
    )
    report = document_diagnostic_service.inspect_document(
        "normalize", {"document": source}
    )
    assert observed == [source]
    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["data"]["meta"] == {}
    assert source == {"node_type": "DocumentObject", "blocks": []}


def test_diagnostic_contract_reuses_private_worker_auth_and_route(monkeypatch):
    observed = []

    def fake_post(path, payload):
        observed.append((path, payload))
        return {
            "ok": True,
            "contract": {"service": "butex-document", "routes": {"normalize": "/v1/document/normalize"}},
        }

    monkeypatch.setattr(document_diagnostic_service.butex_worker_client, "_post", fake_post)
    report = document_diagnostic_service.inspect_document("diagnose_contract", {})
    assert report["ok"] is True
    assert report["data"]["routes"]["normalize"] == "/v1/document/normalize"
    assert observed == [("/v1/document/diagnostics/contract", {})]


def test_expected_validation_error_is_observed_failure_not_success(monkeypatch):
    def invalid(_document):
        raise HTTPException(status_code=422, detail={"code": "invalid_document", "message": "Invalid fixture"})

    monkeypatch.setattr(document_diagnostic_service.butex_worker_client, "normalize_document", invalid)
    report = document_diagnostic_service.inspect_document(
        "normalize", {"document": {"node_type": "Bad", "blocks": []}}
    )
    assert report["status"] == "failed"
    assert report["status_code"] == 422
    assert report["error"]["code"] == "invalid_document"


def test_downstream_worker_absence_is_blocked_not_passed(monkeypatch):
    def unreachable(_document):
        raise HTTPException(status_code=503, detail="worker not configured")

    monkeypatch.setattr(document_diagnostic_service.butex_worker_client, "normalize_document", unreachable)
    report = document_diagnostic_service.inspect_document(
        "normalize", {"document": {"node_type": "DocumentObject", "blocks": []}}
    )
    assert report["status"] == "blocked"
    assert report["ok"] is False
    assert report["human_action"]


def test_diagnostic_schema_rejects_arbitrary_operations():
    try:
        DocumentDiagnosticRequest(operation="arbitrary_http_post", payload={})
    except ValidationError:
        pass
    else:
        raise AssertionError("Document diagnostic must reject arbitrary worker actions")


def test_diagnostic_router_is_dev_mode_gated(monkeypatch):
    monkeypatch.setattr(dev_diagnostics.settings, "dev_mode", False)
    payload = DocumentDiagnosticRequest(
        operation="normalize",
        payload={"document": {"node_type": "DocumentObject", "blocks": []}},
    )
    try:
        dev_diagnostics.inspect_document(payload, actor=object())
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("DEV_MODE-disabled diagnostic unexpectedly succeeded")


def test_diagnostic_router_rejects_oversized_fixture(monkeypatch):
    monkeypatch.setattr(dev_diagnostics.settings, "dev_mode", True)
    payload = DocumentDiagnosticRequest(
        operation="normalize", payload={"document": {"value": "x" * 132_000}}
    )
    try:
        dev_diagnostics.inspect_document(payload, actor=object())
    except HTTPException as exc:
        assert exc.status_code == 413
    else:
        raise AssertionError("Oversized synthetic fixture unexpectedly accepted")
