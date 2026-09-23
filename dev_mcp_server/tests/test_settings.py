import pytest

from albayan_dev_mcp.settings import Settings


def test_missing_service_is_explicitly_unconfigured() -> None:
    settings = Settings(_env_file=None)
    service = settings.service("burhan")
    assert service.configured is False
    assert service.url_env == "BURHAN_DEV_URL"


def test_service_origin_rejects_embedded_credentials() -> None:
    settings = Settings(_env_file=None, burhan_dev_url="https://user:pass@example.com")
    with pytest.raises(ValueError, match="embedded credentials"):
        settings.service("burhan")


def test_service_origin_rejects_path_prefix() -> None:
    settings = Settings(_env_file=None, butex_dev_url="https://example.com/internal")
    with pytest.raises(ValueError, match="without a path prefix"):
        settings.service("butex")


def test_remote_http_auth_configuration_fails_closed_when_incomplete() -> None:
    settings = Settings(_env_file=None, clerk_issuer_url="https://clerk.example")

    assert settings.remote_auth_configured is False
    with pytest.raises(RuntimeError, match="CLERK_SECRET_KEY, DEV_MCP_RESOURCE_URL"):
        settings.require_remote_auth_configuration()


def test_remote_http_auth_configuration_is_complete() -> None:
    settings = Settings(
        _env_file=None,
        clerk_issuer_url="https://clerk.example",
        clerk_secret_key="sk_test_example",
        dev_mcp_resource_url="https://dev-mcp.example/mcp",
    )

    assert settings.remote_auth_configured is True
    settings.require_remote_auth_configuration()
