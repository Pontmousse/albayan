import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.core.config import Settings


VALID_EMAIL_SETTINGS = {
    "RESEND_API_KEY": "re_secret-value-that-must-not-leak",
    "EMAIL_FROM": "مجلة البيان <mail@example.com>",
    "EMAIL_REPLY_TO": "مجلة البيان <contact@example.com>",
    "RESEND_WELCOME_TEMPLATE": "welcome-ar",
    "RESEND_APP_INVITATION_TEMPLATE": "app-invitation-ar",
    "RESEND_AUTH_VERIFICATION_TEMPLATE": "auth-verification-code-ar",
    "RESEND_PASSWORD_RESET_TEMPLATE": "password-reset-ar",
    "FRONTEND_BASE_URL": "https://albayan.example/",
    "EMAIL_ASSET_BASE_URL": "https://albayan.example/email/",
}

SETTING_FIELDS = {
    "RESEND_API_KEY": "resend_api_key",
    "EMAIL_FROM": "email_from",
    "EMAIL_REPLY_TO": "email_reply_to",
    "RESEND_WELCOME_TEMPLATE": "resend_welcome_template",
    "RESEND_APP_INVITATION_TEMPLATE": "resend_app_invitation_template",
    "RESEND_AUTH_VERIFICATION_TEMPLATE": "resend_auth_verification_template",
    "RESEND_PASSWORD_RESET_TEMPLATE": "resend_password_reset_template",
    "FRONTEND_BASE_URL": "frontend_base_url",
    "EMAIL_ASSET_BASE_URL": "email_asset_base_url",
    "DEV_MODE": "dev_mode",
}


def make_settings(**overrides: str) -> Settings:
    values = VALID_EMAIL_SETTINGS | overrides
    fields = {SETTING_FIELDS[name]: value for name, value in values.items()}
    return Settings(_env_file=None, **fields)


class EmailSettingsTests(unittest.TestCase):
    def test_empty_email_group_disables_delivery(self) -> None:
        settings = Settings(_env_file=None)

        self.assertFalse(settings.email_enabled)

    def test_valid_production_configuration_is_normalized(self) -> None:
        settings = make_settings()

        self.assertTrue(settings.email_enabled)
        self.assertEqual(settings.email_from, "مجلة البيان <mail@example.com>")
        self.assertEqual(
            settings.email_reply_to,
            "مجلة البيان <contact@example.com>",
        )
        self.assertEqual(settings.email_reply_to_address, "contact@example.com")
        self.assertEqual(settings.resend_welcome_template, "welcome-ar")
        self.assertEqual(
            settings.resend_app_invitation_template,
            "app-invitation-ar",
        )
        self.assertEqual(
            settings.resend_auth_verification_template,
            "auth-verification-code-ar",
        )
        self.assertEqual(settings.resend_password_reset_template, "password-reset-ar")
        self.assertEqual(settings.frontend_base_url, "https://albayan.example")
        self.assertEqual(
            settings.email_asset_base_url,
            "https://albayan.example/email",
        )

    def test_documented_environment_variable_names_are_loaded(self) -> None:
        with patch.dict("os.environ", VALID_EMAIL_SETTINGS, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.resend_welcome_template, "welcome-ar")
        self.assertEqual(
            settings.resend_app_invitation_template,
            "app-invitation-ar",
        )
        self.assertEqual(
            settings.resend_auth_verification_template,
            "auth-verification-code-ar",
        )
        self.assertEqual(settings.resend_password_reset_template, "password-reset-ar")
        self.assertEqual(
            settings.resend_api_key.get_secret_value(),
            VALID_EMAIL_SETTINGS["RESEND_API_KEY"],
        )

    def test_enabled_email_requires_the_complete_group(self) -> None:
        for missing in (
            "RESEND_API_KEY",
            "EMAIL_FROM",
            "EMAIL_REPLY_TO",
            "RESEND_WELCOME_TEMPLATE",
            "RESEND_APP_INVITATION_TEMPLATE",
            "RESEND_AUTH_VERIFICATION_TEMPLATE",
            "RESEND_PASSWORD_RESET_TEMPLATE",
            "FRONTEND_BASE_URL",
            "EMAIL_ASSET_BASE_URL",
        ):
            with self.subTest(missing=missing):
                with self.assertRaises(ValidationError) as raised:
                    make_settings(**{missing: "   "})

                error = str(raised.exception)
                self.assertIn(missing, error)
                self.assertNotIn(VALID_EMAIL_SETTINGS["RESEND_API_KEY"], error)

    def test_mailbox_identities_are_validated(self) -> None:
        for field in ("EMAIL_FROM", "EMAIL_REPLY_TO"):
            for malformed in (
                "not-an-email",
                "Missing address <>",
                "two@example.com extra",
                "Header <valid@example.com>\nBcc: hidden@example.com",
            ):
                with self.subTest(field=field, malformed=malformed):
                    with self.assertRaisesRegex(ValidationError, field):
                        make_settings(**{field: malformed})

    def test_urls_must_be_absolute_clean_base_urls(self) -> None:
        for field in ("FRONTEND_BASE_URL", "EMAIL_ASSET_BASE_URL"):
            with self.subTest(field=field, kind="relative"):
                with self.assertRaisesRegex(ValidationError, "absolute"):
                    make_settings(**{field: "/relative/path"})
            with self.subTest(field=field, kind="query"):
                with self.assertRaisesRegex(ValidationError, "clean base URL"):
                    make_settings(**{field: "https://albayan.example/?token=value"})

    def test_production_urls_must_use_https(self) -> None:
        for field in ("FRONTEND_BASE_URL", "EMAIL_ASSET_BASE_URL"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValidationError, "HTTPS"):
                    make_settings(**{field: "http://albayan.example"})

    def test_development_permits_local_http_urls(self) -> None:
        settings = make_settings(
            DEV_MODE="true",
            FRONTEND_BASE_URL="http://localhost:3000/",
            EMAIL_ASSET_BASE_URL="http://127.0.0.1:8080/assets/",
        )

        self.assertEqual(settings.frontend_base_url, "http://localhost:3000")
        self.assertEqual(
            settings.email_asset_base_url,
            "http://127.0.0.1:8080/assets",
        )

    def test_resend_key_format_is_validated_without_leaking_the_key(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            make_settings(RESEND_API_KEY="secret-value-that-must-not-leak")

        error = str(raised.exception)
        self.assertIn("RESEND_API_KEY", error)
        self.assertNotIn("secret-value-that-must-not-leak", error)


if __name__ == "__main__":
    unittest.main()
