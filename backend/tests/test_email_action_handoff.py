import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException

from app.services import email_action_handoff


class EmailActionHandoffTests(unittest.TestCase):
    def test_round_trip_signed_token(self) -> None:
        now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
        with patch.object(
            email_action_handoff.settings,
            "clerk_secret_key",
            "sk_test_handoff_secret",
        ):
            token = email_action_handoff.create_handoff_token(
                kind="app_invitation",
                subject="inv_test",
                expires_at=now + timedelta(hours=1),
            )
            claims = email_action_handoff.verify_handoff_token(
                token,
                expected_kind="app_invitation",
                now=now,
            )

        self.assertEqual(claims.subject, "inv_test")
        self.assertEqual(claims.kind, "app_invitation")

    def test_tampered_token_is_rejected(self) -> None:
        now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
        with patch.object(
            email_action_handoff.settings,
            "clerk_secret_key",
            "sk_test_handoff_secret",
        ):
            token = email_action_handoff.create_handoff_token(
                kind="app_invitation",
                subject="inv_test",
                expires_at=now + timedelta(hours=1),
            )
            payload, signature = token.split(".", 1)
            tampered = f"{payload[:-1]}A.{signature}"
            with self.assertRaises(HTTPException) as raised:
                email_action_handoff.verify_handoff_token(
                    tampered,
                    expected_kind="app_invitation",
                    now=now,
                )

        self.assertEqual(raised.exception.status_code, 404)

    def test_expired_token_is_rejected(self) -> None:
        now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
        with patch.object(
            email_action_handoff.settings,
            "clerk_secret_key",
            "sk_test_handoff_secret",
        ):
            token = email_action_handoff.create_handoff_token(
                kind="app_invitation",
                subject="inv_test",
                expires_at=now - timedelta(seconds=1),
            )
            with self.assertRaises(HTTPException) as raised:
                email_action_handoff.verify_handoff_token(
                    token,
                    expected_kind="app_invitation",
                    now=now,
                )

        self.assertEqual(raised.exception.status_code, 410)


if __name__ == "__main__":
    unittest.main()
