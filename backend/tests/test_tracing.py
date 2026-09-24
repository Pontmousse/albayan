from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.tracing import TRACE_HEADER, TraceContextMiddleware, current_trace_id, trace_headers


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TraceContextMiddleware)

    @app.get("/probe")
    def probe() -> dict[str, object]:
        return {
            "trace_id": current_trace_id(),
            "outbound_headers": trace_headers(),
        }

    return app


def test_backend_preserves_valid_incoming_trace_id() -> None:
    with TestClient(_app()) as client:
        response = client.get("/probe", headers={TRACE_HEADER: "trace-browser-123"})

    assert response.status_code == 200
    assert response.headers[TRACE_HEADER] == "trace-browser-123"
    assert response.json()["trace_id"] == "trace-browser-123"
    assert response.json()["outbound_headers"] == {TRACE_HEADER: "trace-browser-123"}


def test_backend_generates_trace_id_when_missing() -> None:
    with TestClient(_app()) as client:
        response = client.get("/probe")

    trace_id = response.headers[TRACE_HEADER]
    assert trace_id
    assert response.json()["trace_id"] == trace_id


def test_backend_replaces_invalid_trace_id_instead_of_reflecting_it() -> None:
    with TestClient(_app()) as client:
        response = client.get("/probe", headers={TRACE_HEADER: "bad trace id"})

    assert response.status_code == 200
    assert response.headers[TRACE_HEADER] != "bad trace id"
    assert response.json()["trace_id"] == response.headers[TRACE_HEADER]
