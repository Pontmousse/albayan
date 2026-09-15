from __future__ import annotations

import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi import HTTPException

from app.services import clerk_email_webhook_service


class ClerkEmailWebhookTests(unittest.TestCase):
    def test_ignores_delivered_by_clerk_email(self) -> None:
        result = clerk_email_webhook_service.handle_clerk_webhook(
            {
                "type": "email.created",
                "data": {
                    "id": "email_1",
                    "slug": "password_changed",
                    "to_email_address": "user@example.com",
                    "delivered_by_clerk": True,
                    "data": {},
                },
            }
        )

        self.assertEqual(result, {"ok": True, "ignored": True})

    def test_unknown_clerk_email_slug_is_ignored(self) -> None:
        result = clerk_email_webhook_service.handle_clerk_webhook(
            {
                "type": "email.created",
                "data": {
                    "id": "email_unknown",
                    "slug": "some_future_template",
                    "to_email_address": "user@example.com",
                    "delivered_by_clerk": False,
                    "data": {},
                },
            }
        )

        self.assertEqual(result, {"ok": True, "ignored": True})

    def test_verification_code_uses_resend_template(self) -> None:
        with patch.object(
            clerk_email_webhook_service.email_service,
            "send_auth_verification_email",
            return_value="email_resend",
        ) as send:
            result = clerk_email_webhook_service.handle_clerk_webhook(
                {
                    "type": "email.created",
                    "data": {
                        "id": "email_1",
                        "slug": "verification_code",
                        "to_email_address": "user@example.com",
                        "delivered_by_clerk": False,
                        "data": {"otp_code": "123456"},
                    },
                }
            )

        send.assert_called_once_with(
            to="user@example.com",
            otp_code="123456",
            idempotency_key="clerk-email/email_1",
        )
        self.assertEqual(result, {"ok": True, "message_id": "email_resend"})

    def test_password_reset_code_uses_resend_template(self) -> None:
        with patch.object(
            clerk_email_webhook_service.email_service,
            "send_password_reset_email",
            return_value="email_resend",
        ) as send:
            result = clerk_email_webhook_service.handle_clerk_webhook(
                {
                    "type": "emails.created",
                    "data": {
                        "id": "email_2",
                        "slug": "reset_password_code",
                        "to_email_address": "user@example.com",
                        "delivered_by_clerk": False,
                        "data": {"otp_code": "654321"},
                    },
                }
            )

        send.assert_called_once_with(
            to="user@example.com",
            otp_code="654321",
            idempotency_key="clerk-email/email_2",
        )
        self.assertEqual(result, {"ok": True, "message_id": "email_resend"})

    def test_security_notifications_use_albayan_resend_templates(self) -> None:
        # These are Clerk's current security-template slugs. Keeping them in one
        # table makes contract drift obvious if Clerk changes a template slug.
        cases = (
            ("account_locked", "send_account_locked_email"),
            ("password_changed", "send_password_changed_email"),
            ("password_removed", "send_password_removed_email"),
            ("primary_email_address_changed", "send_primary_email_changed_email"),
            ("new_device_sign_in", "send_new_device_sign_in_email"),
        )

        for index, (slug, sender_name) in enumerate(cases, start=1):
            with self.subTest(slug=slug):
                with patch.object(
                    clerk_email_webhook_service.clerk_security_email_service,
                    sender_name,
                    return_value=f"email_resend_{index}",
                ) as send:
                    result = clerk_email_webhook_service.handle_clerk_webhook(
                        {
                            "type": "email.created",
                            "data": {
                                "id": f"email_security_{index}",
                                "slug": slug,
                                "to_email_address": "user@example.com",
                                "delivered_by_clerk": False,
                                "data": {},
                            },
                        }
                    )

                send.assert_called_once_with(
                    to="user@example.com",
                    idempotency_key=f"clerk-email/email_security_{index}",
                )
                self.assertEqual(
                    result,
                    {"ok": True, "message_id": f"email_resend_{index}"},
                )

    def test_supported_otp_email_without_code_fails_safely(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            clerk_email_webhook_service.handle_clerk_webhook(
                {
                    "type": "email.created",
                    "data": {
                        "id": "email_1",
                        "slug": "verification_code",
                        "to_email_address": "user@example.com",
                        "delivered_by_clerk": False,
                        "data": {},
                    },
                }
            )

        self.assertEqual(raised.exception.status_code, 422)
        self.assertNotIn("123456", str(raised.exception.detail))

    def test_security_notification_does_not_require_otp_metadata(self) -> None:
        with patch.object(
            clerk_email_webhook_service.clerk_security_email_service,
            "send_password_changed_email",
            return_value="email_resend",
        ):
            result = clerk_email_webhook_service.handle_clerk_webhook(
                {
                    "type": "email.created",
                    "data": {
                        "id": "email_security",
                        "slug": "password_changed",
                        "to_email_address": "user@example.com",
                        "delivered_by_clerk": False,
                    },
                }
            )

        self.assertEqual(result, {"ok": True, "message_id": "email_resend"})

    def test_webhook_signature_is_required(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    clerk_email_webhook_service.settings,
                    "clerk_webhook_signing_secret",
                    "",
                )
            )

            with self.assertRaises(HTTPException) as raised:
                clerk_email_webhook_service.verify_clerk_webhook(
                    payload=b"{}",
                    headers={},
                )

        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
