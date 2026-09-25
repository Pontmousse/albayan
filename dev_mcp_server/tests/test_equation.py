import httpx
import pytest

from albayan_dev_mcp.equation import (
    DIAGNOSTIC_PATH,
    EquationDiagnosticClient,
    compare_reports,
    fixture_by_id,
    json_diff,
    load_equation_fixtures,
    stage_matrix,
)
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import InMemoryTraceSource


def _report(trace_id: str = "trace-equation") -> dict:
    return {
        "ok": True,
        "partial": False,
        "trace_id": trace_id,
        "stages": {
            "canonical_input": {"available": True, "ok": True, "data": {"latex": "x"}},
            "burhan_conversion": {
                "available": True,
                "ok": True,
                "data": {
                    "english_json": {"node_type": "MathObject"},
                    "arabic_json": {"node_type": "MathObject"},
                    "mappings": {"x": "س"},
                    "warnings": [],
                    "duration_ms": 2.5,
                },
            },
            "albayan_projection": {
                "available": True,
                "ok": True,
                "data": {"editor_math_object": {"node_type": "MathObject"}},
            },
            "document2_command": {"available": True, "ok": True, "data": {}},
            "headless_butex_validation": {
                "available": True,
                "ok": True,
                "data": {
                    "ok": True,
                    "stage": "mathObjectToEditorSession",
                    "editable": True,
                    "english_latex": "x",
                },
            },
            "reverse_conversion": {
                "available": True,
                "ok": True,
                "data": {"canonical_latex": "x"},
            },
            "browser_validation": {
                "available": False,
                "ok": None,
                "reason": "separate_playwright_observation_plane",
            },
        },
    }


def test_fixture_corpus_contains_required_adjacency_regressions() -> None:
    fixtures = load_equation_fixtures()
    ids = {fixture["id"] for fixture in fixtures}
    sources = {fixture["source"] for fixture in fixtures}

    assert len(fixtures) >= 35
    assert {"dx", "df", "kx", "k x", "Ax", "xA", "abc", "\\frac{df}{dx}"} <= sources
    assert {"adjacent-dx", "adjacent-df", "adjacent-kx", "df-over-dx"} <= ids
    assert fixture_by_id("cases")["display"] is True


def test_stage_matrix_distinguishes_browser_unavailability_from_pipeline_failure() -> None:
    matrix = stage_matrix(_report())
    assert matrix["burhan_conversion"] == "pass"
    assert matrix["headless_butex_validation"] == "pass"
    assert matrix["browser_validation"] == "unavailable"


def test_json_diff_is_bounded_and_structural() -> None:
    differences = json_diff(
        {"a": [1, 2], "b": {"x": "left"}},
        {"a": [1, 3, 4], "b": {"x": "right"}},
        limit=2,
    )
    assert len(differences) == 2
    assert all("path" in row for row in differences)


def test_model_comparison_reports_structured_differences() -> None:
    heuristic = _report("trace-shared")
    cheap = _report("trace-shared")
    cheap["stages"]["burhan_conversion"]["data"]["mappings"] = {"x": "ص"}
    medium = _report("trace-shared")

    comparison = compare_reports(
        {"heuristic": heuristic, "cheap": cheap, "medium": medium}
    )

    assert comparison["tiers"]["heuristic"]["differences_from_heuristic"] == []
    assert any(
        row["path"].endswith("mappings.x")
        for row in comparison["tiers"]["cheap"]["differences_from_heuristic"]
    )


@pytest.mark.asyncio
async def test_equation_client_uses_only_fixed_authenticated_endpoint_and_trace() -> None:
    trace_source = InMemoryTraceSource()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == DIAGNOSTIC_PATH
        assert request.headers["Authorization"] == "Bearer dev-token"
        assert request.headers["X-Trace-Id"] == "trace-equation"
        payload = __import__("json").loads(request.content)
        assert payload == {
            "latex": "x",
            "display": False,
            "model_tier": "heuristic",
        }
        return httpx.Response(
            200,
            headers={"X-Trace-Id": "trace-equation"},
            json=_report("trace-equation"),
        )

    settings = Settings(
        _env_file=None,
        albayan_dev_url="https://dev.example",
        albayan_dev_token="dev-token",
    )
    client = EquationDiagnosticClient(
        settings,
        transport=httpx.MockTransport(handler),
        trace_source=trace_source,
    )
    result = await client.inspect(
        latex="x",
        display=False,
        model_tier="heuristic",
        trace_id="trace-equation",
    )

    assert result["ok"] is True
    assert result["correlation_preserved"] is True
    assert [event.status for event in trace_source.get_trace("trace-equation")] == [
        "started",
        "ok",
    ]


@pytest.mark.asyncio
async def test_equation_client_reports_missing_auth_without_network_call() -> None:
    client = EquationDiagnosticClient(
        Settings(_env_file=None, albayan_dev_url="https://dev.example")
    )
    result = await client.inspect(
        latex="x",
        display=False,
        model_tier="heuristic",
    )

    assert result["blocked"] is True
    assert result["reason"] == "missing_configuration"
    assert "ALBAYAN_DEV_TOKEN" in result["missing"]
