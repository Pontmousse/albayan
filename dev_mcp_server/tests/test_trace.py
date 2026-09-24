import httpx
import pytest

from albayan_dev_mcp.client import DevHttpClient
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import InMemoryTraceSource, validate_trace_id


def test_trace_source_preserves_event_order_and_bounds_retention() -> None:
    source = InMemoryTraceSource(max_traces=2, max_events_per_trace=2)
    source.record(trace_id="trace-a", service="dev_mcp", stage="one", status="started")
    source.record(trace_id="trace-a", service="albayan", stage="two", status="ok")
    source.record(trace_id="trace-a", service="burhan", stage="three", status="ok")

    events = source.get_trace("trace-a")
    assert [event.sequence for event in events] == [2, 3]
    assert [event.stage for event in events] == ["two", "three"]

    source.record(trace_id="trace-b", service="dev_mcp", stage="one", status="ok")
    source.record(trace_id="trace-c", service="dev_mcp", stage="one", status="ok")
    assert source.get_trace("trace-a") == []
    assert [row["trace_id"] for row in source.list_recent(limit=10)] == [
        "trace-c",
        "trace-b",
    ]


def test_trace_id_validation_rejects_unbounded_or_header_like_values() -> None:
    assert validate_trace_id("trace-123") == "trace-123"
    with pytest.raises(ValueError):
        validate_trace_id("bad trace id")
    with pytest.raises(ValueError):
        validate_trace_id("x\r\nAuthorization: secret")


@pytest.mark.asyncio
async def test_http_client_propagates_trace_id_and_records_events() -> None:
    source = InMemoryTraceSource()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Trace-Id"] == "trace-123"
        return httpx.Response(
            200,
            headers={"X-Trace-Id": "trace-123", "content-type": "application/json"},
            json={"ok": True},
        )

    settings = Settings(_env_file=None, albayan_dev_url="https://dev.example")
    client = DevHttpClient(
        settings,
        transport=httpx.MockTransport(handler),
        trace_source=source,
    )
    result = await client.request(
        service="albayan",
        method="GET",
        path="/health",
        trace_id="trace-123",
    )

    assert result["trace_id"] == "trace-123"
    assert result["correlation_preserved"] is True
    events = source.get_trace("trace-123")
    assert [event.stage for event in events] == ["http_request", "http_response"]
    assert [event.status for event in events] == ["started", "ok"]


@pytest.mark.asyncio
async def test_missing_service_still_returns_trace_id_and_blocked_event() -> None:
    source = InMemoryTraceSource()
    client = DevHttpClient(Settings(_env_file=None), trace_source=source)

    result = await client.request(
        service="burhan",
        method="GET",
        path="/",
        trace_id="trace-missing",
    )

    assert result["trace_id"] == "trace-missing"
    assert result["blocked"] is True
    assert source.get_trace("trace-missing")[-1].status == "blocked"
