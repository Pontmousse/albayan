import httpx
import pytest

from albayan_dev_mcp.client import DevHttpClient, _validate_relative_path
from albayan_dev_mcp.settings import Settings


def test_rejects_arbitrary_url() -> None:
    with pytest.raises(ValueError):
        _validate_relative_path("https://evil.example/")
    with pytest.raises(ValueError):
        _validate_relative_path("//evil.example/path")


@pytest.mark.asyncio
async def test_missing_configuration_returns_human_action() -> None:
    client = DevHttpClient(Settings(_env_file=None))
    result = await client.request(service="burhan", method="GET", path="/")
    assert result["blocked"] is True
    assert result["reason"] == "missing_configuration"
    assert result["missing"] == ["BURHAN_DEV_URL"]
    assert "Configure BURHAN_DEV_URL" in result["human_action"]


@pytest.mark.asyncio
async def test_response_is_bounded_and_secret_fields_are_redacted() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "dev.example"
        assert request.headers["Authorization"] == "Bearer private-token"
        return httpx.Response(
            200,
            headers={"content-type": "application/json", "set-cookie": "secret=1"},
            json={"token": "server-secret", "safe": "x" * 100},
        )

    settings = Settings(
        _env_file=None,
        burhan_dev_url="https://dev.example",
        burhan_dev_token="private-token",
        dev_mcp_max_response_bytes=1024,
    )
    client = DevHttpClient(settings, transport=httpx.MockTransport(handler))
    result = await client.request(service="burhan", method="GET", path="/debug")
    assert result["ok"] is True
    assert result["body"]["token"] == "[REDACTED]"
    assert "set-cookie" not in result["headers"]


@pytest.mark.asyncio
async def test_health_counts_http_error_as_reachable() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    settings = Settings(_env_file=None, albayan_dev_url="http://dev.example")
    client = DevHttpClient(settings, transport=httpx.MockTransport(handler))
    result = await client.probe("albayan")
    assert result["configured"] is True
    assert result["reachable"] is True
    assert result["status_code"] == 404
