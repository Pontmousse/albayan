import pytest
from pydantic import ValidationError

from app.core.config import Settings


VALID_EMAIL_SETTINGS = {
    "EMAIL_ENABLED": "true",
    "RESEND_API_KEY": "re_secret-value-that-must-not-leak",
    "EMAIL_FROM": "مجلة البيان <noreply@example.com>",
    "EMAIL_REPLY_TO": "Editorial Team <editors@example.com>",
    "RESEND_WELCOME_TEMPLATE": "welcome-template",
    "FRONTEND_BASE_URL": "https://albayan.example/",
    "EMAIL_ASSET_BASE_URL": "https://assets.albayan.example/email/",
}


def make_settings(**overrides: str) -> Settings:
    values = VALID_EMAIL_SETTINGS | overrides
    return Settings(_env_file=None, **values)


def test_valid_production_email_configuration_is_normalized() -> None:
    settings = make_settings()

    assert settings.email_from == "مجلة البيان <noreply@example.com>"
    assert settings.email_reply_to == "Editorial Team <editors@example.com>"
    assert settings.resend_welcome_template_id == "welcome-template"
    assert settings.frontend_base_url == "https://albayan.example"
    assert settings.email_asset_base_url == "https://assets.albayan.example/email"


@pytest.mark.parametrize(
    "missing",
    [
        "RESEND_API_KEY",
        "EMAIL_FROM",
        "EMAIL_REPLY_TO",
        "RESEND_WELCOME_TEMPLATE",
        "FRONTEND_BASE_URL",
        "EMAIL_ASSET_BASE_URL",
    ],
)
def test_enabled_email_requires_every_group_field(missing: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        make_settings(**{missing: "   "})

    error = str(exc_info.value)
    assert missing in error
    assert VALID_EMAIL_SETTINGS["RESEND_API_KEY"] not in error


@pytest.mark.parametrize("field", ["EMAIL_FROM", "EMAIL_REPLY_TO"])
@pytest.mark.parametrize(
    "malformed", ["not-an-email", "Missing address <>", "two@example.com extra"]
)
def test_email_mailboxes_must_be_valid(field: str, malformed: str) -> None:
    with pytest.raises(ValidationError, match=field):
        make_settings(**{field: malformed})


@pytest.mark.parametrize("field", ["FRONTEND_BASE_URL", "EMAIL_ASSET_BASE_URL"])
def test_email_urls_must_be_absolute(field: str) -> None:
    with pytest.raises(ValidationError, match="absolute"):
        make_settings(**{field: "/relative/path"})


@pytest.mark.parametrize("field", ["FRONTEND_BASE_URL", "EMAIL_ASSET_BASE_URL"])
def test_production_email_urls_must_use_https(field: str) -> None:
    with pytest.raises(ValidationError, match="HTTPS"):
        make_settings(**{field: "http://albayan.example"})


def test_development_permits_local_http_urls() -> None:
    settings = make_settings(
        DEV_MODE="true",
        FRONTEND_BASE_URL="http://localhost:3000/",
        EMAIL_ASSET_BASE_URL="http://127.0.0.1:8080/assets/",
    )

    assert settings.frontend_base_url == "http://localhost:3000"
    assert settings.email_asset_base_url == "http://127.0.0.1:8080/assets"


def test_validation_errors_redact_resend_api_key() -> None:
    with pytest.raises(ValidationError) as exc_info:
        make_settings(EMAIL_FROM="invalid")

    assert VALID_EMAIL_SETTINGS["RESEND_API_KEY"] not in str(exc_info.value)
