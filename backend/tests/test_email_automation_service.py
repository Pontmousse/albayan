from datetime import UTC, datetime, timedelta
import uuid
import unittest
from unittest.mock import Mock, patch

from app.models.enums import ReviewerAssignmentStatus
from app.services import email_automation_service


class EmailAutomationServiceTests(unittest.TestCase):
    def test_midpoint_review_reminder_marks_assignment_after_send(self) -> None:
        now = datetime(2026, 8, 31, tzinfo=UTC)
        assignment = Mock(
            id=uuid.uuid4(),
            status=ReviewerAssignmentStatus.ACCEPTED,
            invited_at=now - timedelta(days=5),
            review_due_at=now + timedelta(days=4),
            reminder_midpoint_sent_at=None,
            reminder_due_soon_sent_at=None,
        )
        assignment.user.email = "reviewer@example.com"
        assignment.article.title = "عنوان البحث"
        db = Mock()
        db.scalars.return_value.all.return_value = [assignment]

        with patch.object(
            email_automation_service.email_service,
            "send_review_reminder_email",
        ) as send:
            sent = email_automation_service.send_due_review_reminders(db, now=now)

        self.assertEqual(sent, 1)
        self.assertEqual(assignment.reminder_midpoint_sent_at, now)
        self.assertIsNone(assignment.reminder_due_soon_sent_at)
        send.assert_called_once()
        self.assertEqual(db.commit.call_count, 2)

    def test_due_soon_review_reminder_marks_assignment_after_send(self) -> None:
        now = datetime(2026, 8, 31, tzinfo=UTC)
        assignment = Mock(
            id=uuid.uuid4(),
            status=ReviewerAssignmentStatus.ACCEPTED,
            invited_at=now - timedelta(days=8),
            review_due_at=now + timedelta(hours=12),
            reminder_midpoint_sent_at=now - timedelta(days=3),
            reminder_due_soon_sent_at=None,
        )
        assignment.user.email = "reviewer@example.com"
        assignment.article.title = "عنوان البحث"
        db = Mock()
        db.scalars.return_value.all.return_value = [assignment]

        with patch.object(
            email_automation_service.email_service,
            "send_review_reminder_email",
        ):
            sent = email_automation_service.send_due_review_reminders(db, now=now)

        self.assertEqual(sent, 1)
        self.assertEqual(assignment.reminder_due_soon_sent_at, now)
        self.assertEqual(db.commit.call_count, 2)

    def test_unread_digest_updates_state_after_send(self) -> None:
        now = datetime(2026, 8, 31, tzinfo=UTC)
        user = Mock(id=uuid.uuid4(), email="user@example.com")
        db = Mock()
        db.execute.return_value.all.return_value = [(user, 6)]
        db.get.return_value = None

        with patch.object(
            email_automation_service.email_service,
            "send_unread_notifications_digest_email",
        ) as send:
            sent = email_automation_service.send_unread_notification_digests(
                db,
                now=now,
            )

        self.assertEqual(sent, 1)
        send.assert_called_once()
        db.add.assert_called_once()
        self.assertEqual(db.add.call_args.args[0].last_unread_digest_sent_at, now)
        db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
