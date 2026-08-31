from __future__ import annotations

import uuid
import unittest
from unittest.mock import Mock

from app.models.enums import AccountDeletionRequestStatus
from app.services import account_deletion_service


class AccountDeletionRequestTests(unittest.TestCase):
    def test_create_requires_recent_reverification(self) -> None:
        with self.assertRaises(
            account_deletion_service.RequiresReverificationError
        ):
            account_deletion_service.create_deletion_request(
                Mock(),
                user=Mock(),
                session_claims={"fva": [42, -1]},
                reason=None,
            )

    def test_create_stores_pending_request(self) -> None:
        db = Mock()
        db.scalar.return_value = None
        user = Mock(
            id=uuid.uuid4(),
            email="author@example.com",
        )

        request, created = account_deletion_service.create_deletion_request(
            db,
            user=user,
            session_claims={"fva": [0, -1]},
            reason="أريد حذف الحساب",
        )

        self.assertTrue(created)
        self.assertEqual(request.user_id, user.id)
        self.assertEqual(request.email_snapshot, "author@example.com")
        self.assertEqual(request.reason, "أريد حذف الحساب")
        self.assertEqual(request.status, AccountDeletionRequestStatus.PENDING)
        db.add.assert_called_once_with(request)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(request)

    def test_existing_pending_request_is_idempotent(self) -> None:
        existing = Mock()
        db = Mock()
        db.scalar.return_value = existing

        request, created = account_deletion_service.create_deletion_request(
            db,
            user=Mock(id=uuid.uuid4(), email="author@example.com"),
            session_claims={"fva": [0, -1]},
            reason=None,
        )

        self.assertFalse(created)
        self.assertIs(request, existing)
        db.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
