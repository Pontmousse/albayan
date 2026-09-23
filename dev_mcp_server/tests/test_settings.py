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
