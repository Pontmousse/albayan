from __future__ import annotations

import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from app.core.clerk import AuthContext
from app.services import user_service


class UserServiceEmailTests(unittest.TestCase):
    def test_missing_welcome_email_config_does_not_block_user_creation(self) -> None:
        db = Mock()
        db.scalar.return_value = None
        auth = AuthContext(
            clerk_id="user_test",
            email="author@example.com",
            full_name="د. أحمد",
        )

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(user_service.email_service.settings, "resend_api_key", "")
            )
            stack.enter_context(
                patch.object(user_service.email_service.settings, "email_from", "")
            )
            stack.enter_context(
                patch.object(
                    user_service.email_service.settings,
                    "resend_welcome_template",
                    "",
                )
            )

            user = user_service.get_or_create_user(db, auth)

        self.assertEqual(user.email, "author@example.com")
        self.assertEqual(user.full_name, "د. أحمد")
        db.add.assert_called_once_with(user)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(user)

    def test_existing_user_does_not_receive_welcome_email(self) -> None:
        db = Mock()
        existing = Mock(email="author@example.com")
        db.scalar.return_value = existing
        auth = AuthContext(
            clerk_id="user_test",
            email="author@example.com",
            full_name="د. أحمد",
        )

        with patch.object(user_service, "email_service") as email_service:
            user = user_service.get_or_create_user(db, auth)

        self.assertIs(user, existing)
        email_service.send_welcome_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
