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
                    "slug": "verification_code",
                    "to_email_address": "user@example.com",
                    "delivered_by_clerk": True,
                    "data": {"otp_code": "123456"},
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
            clerk_email_webhook_service.handle_clerk_webhook(
                {
                    "type": "email.created",
                    "data": {
                        "id": "email_2",
                        "slug": "reset_password",
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

    def test_supported_email_without_otp_fails_safely(self) -> None:
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
