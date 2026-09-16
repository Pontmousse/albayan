from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services import clerk_security_email_service


class ClerkSecurityEmailServiceTests(unittest.TestCase):
    def test_security_notice_senders_use_stable_resend_aliases(self) -> None:
        cases = (
            (
                clerk_security_email_service.send_account_locked_email,
                "account-locked-ar",
            ),
            (
                clerk_security_email_service.send_password_changed_email,
                "password-changed-ar",
            ),
            (
                clerk_security_email_service.send_password_removed_email,
                "password-removed-ar",
            ),
            (
                clerk_security_email_service.send_primary_email_changed_email,
                "primary-email-changed-ar",
            ),
            (
                clerk_security_email_service.send_new_device_sign_in_email,
                "new-device-sign-in-ar",
            ),
        )

        for sender, expected_alias in cases:
            with self.subTest(alias=expected_alias):
                with (
                    patch.object(
                        clerk_security_email_service.email_service,
                        "_common_variables",
                        return_value={
                            "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                            "SITE_URL": "https://albayan-journal.org",
                            "CONTACT_EMAIL": "support@albayan-journal.org",
                            "ASSET_BASE_URL": "https://albayan-journal.org/email",
                        },
                    ),
                    patch.object(
                        clerk_security_email_service.email_service,
                        "_send_resend_email",
                        return_value="email_resend",
                    ) as send,
                ):
                    message_id = sender(
                        to="user@example.com",
                        idempotency_key="clerk-email/email_1",
                    )

                self.assertEqual(message_id, "email_resend")
                kwargs = send.call_args.kwargs
                self.assertEqual(kwargs["to"], "user@example.com")
                self.assertEqual(kwargs["template_alias_or_id"], expected_alias)
                self.assertEqual(kwargs["idempotency_key"], "clerk-email/email_1")
                self.assertEqual(
                    kwargs["variables"],
                    {
                        "RECIPIENT_EMAIL": "user@example.com",
                        "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                        "SITE_URL": "https://albayan-journal.org",
                        "CONTACT_EMAIL": "support@albayan-journal.org",
                        "ASSET_BASE_URL": "https://albayan-journal.org/email",
                    },
                )


if __name__ == "__main__":
    unittest.main()
