from __future__ import annotations

import inspect
import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import ANY, MagicMock, Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.enums import IssueCategory, IssueStatus, NotificationType
from app.models.issue import Issue, IssueUpvote
from app.models.notification import Notification
from app.models.user import User
from app.routers import issues, notifications
from app.schemas.issue import IssueCreate
from app.services import (
    issue_service,
    notification_email_policy,
    notification_service,
)


def _user(user_id: uuid.UUID | None = None) -> User:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return User(
        id=user_id or uuid.uuid4(),
        clerk_id="user_test",
        email="test@example.com",
        full_name="Test User",
        affiliation=None,
        bio=None,
        created_at=now,
        updated_at=now,
    )


class NotificationPhase1Tests(unittest.TestCase):
    def test_endpoints_are_human_only(self) -> None:
        self.assertEqual(
            inspect.signature(notifications.list_notifications).parameters[
                "auth"
            ].annotation,
            notifications.AuthDep,
        )
        self.assertEqual(
            inspect.signature(notifications.mark_notification_read).parameters[
                "auth"
            ].annotation,
            notifications.AuthDep,
        )

    def test_service_creates_unread_notification_with_metadata(self) -> None:
        db = Mock()
        user_id = uuid.uuid4()

        row = notification_service.create_notification(
            db,
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title="عنوان",
            body="نص",
            metadata={"kind": "test"},
        )

        self.assertIsInstance(row, Notification)
        self.assertEqual(row.user_id, user_id)
        self.assertEqual(row.type, NotificationType.SYSTEM)
        self.assertEqual(row.metadata_json, {"kind": "test"})
        self.assertFalse(row.is_read)
        self.assertIsNone(row.read_at)
        db.add.assert_called_once_with(row)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(row)

    def test_route_lists_current_users_notifications_only(self) -> None:
        user = _user()
        db = Mock()

        with patch.object(
            notifications, "current_user", return_value=user
        ), patch.object(
            notifications.notification_service,
            "list_notifications",
            return_value=[],
        ) as list_mock:
            response = notifications.list_notifications(
                auth=Mock(), db=db, limit=10
            )

        self.assertEqual(response, [])
        list_mock.assert_called_once_with(db, user.id, 10)

    def test_cannot_mark_another_users_notification_read(self) -> None:
        db = Mock()
        db.scalar.return_value = None

        with self.assertRaises(HTTPException) as raised:
            notification_service.mark_notification_read(
                db, uuid.uuid4(), uuid.uuid4()
            )

        self.assertEqual(raised.exception.status_code, 404)
        db.commit.assert_not_called()

    def test_mark_one_read_sets_timestamp(self) -> None:
        db = Mock()
        row = Notification(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            type=NotificationType.SYSTEM,
            title="عنوان",
            is_read=False,
            metadata_json={},
        )
        db.scalar.return_value = row

        result = notification_service.mark_notification_read(db, row.id, row.user_id)

        self.assertIs(result, row)
        self.assertTrue(row.is_read)
        self.assertIsNotNone(row.read_at)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(row)

    def test_unread_count_uses_scalar_count(self) -> None:
        db = Mock()
        db.scalar.return_value = 3

        self.assertEqual(notification_service.unread_count(db, uuid.uuid4()), 3)

    def test_mark_all_read_returns_updated_count(self) -> None:
        db = Mock()
        result = Mock()
        result.rowcount = 4
        db.execute.return_value = result

        updated = notification_service.mark_all_read(db, uuid.uuid4())

        self.assertEqual(updated, 4)
        db.commit.assert_called_once_with()


class IssuePhase1Tests(unittest.TestCase):
    def test_endpoints_are_human_only(self) -> None:
        self.assertEqual(
            inspect.signature(issues.list_issues).parameters["auth"].annotation,
            issues.AuthDep,
        )
        self.assertEqual(
            inspect.signature(issues.create_issue).parameters["auth"].annotation,
            issues.AuthDep,
        )

    def test_issue_schema_trims_and_validates(self) -> None:
        payload = IssueCreate(
            title="  عنوان  ",
            description="\n وصف البلاغ \n",
            category=IssueCategory.BUG,
        )

        self.assertEqual(payload.title, "عنوان")
        self.assertEqual(payload.description, "وصف البلاغ")

        with self.assertRaises(ValidationError):
            IssueCreate(title="   ", description="وصف", category=IssueCategory.BUG)

        with self.assertRaises(ValidationError):
            IssueCreate(title="عنوان", description=" ", category=IssueCategory.BUG)

    def test_create_issue_sets_defaults(self) -> None:
        db = Mock()
        user_id = uuid.uuid4()

        with patch.object(issue_service, "_recent_issue_count", return_value=0):
            row = issue_service.create_issue(
                db,
                user_id=user_id,
                title="عنوان",
                description="وصف",
                category=IssueCategory.FEATURE_REQUEST,
            )

        self.assertIsInstance(row, Issue)
        self.assertEqual(row.user_id, user_id)
        self.assertEqual(row.status, IssueStatus.OPEN)
        self.assertEqual(row.upvote_count, 0)
        db.add.assert_called_once_with(row)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(row)

    def test_create_issue_rate_limit_blocks_sixth_recent_issue(self) -> None:
        db = Mock()

        with patch.object(issue_service, "_recent_issue_count", return_value=5):
            with self.assertRaises(HTTPException) as raised:
                issue_service.create_issue(
                    db,
                    user_id=uuid.uuid4(),
                    title="عنوان",
                    description="وصف",
                    category=IssueCategory.FEEDBACK,
                )

        self.assertEqual(raised.exception.status_code, 429)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_route_lists_all_issues_and_marks_current_user_upvote_state(self) -> None:
        current = _user()
        reporter = _user()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=reporter.id,
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=1,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        issue.reporter = reporter
        issue.images = []

        with patch.object(issues, "current_user", return_value=current), patch.object(
            issues.issue_service, "list_issues", return_value=[issue]
        ) as list_mock, patch.object(
            issues.issue_service,
            "upvoted_issue_ids",
            return_value={issue.id},
        ) as upvoted_mock:
            response = issues.list_issues(
                auth=Mock(),
                db=MagicMock(),
                status=None,
                category=None,
                sort="date",
                direction="desc",
            )

        self.assertEqual(response[0].id, issue.id)
        self.assertTrue(response[0].current_user_upvoted)
        list_mock.assert_called_once_with(
            ANY,
            status=None,
            category=None,
            sort="date",
            direction="desc",
        )
        upvoted_mock.assert_called_once()

    def test_route_passes_issue_filters_and_sorting(self) -> None:
        current = _user()
        db = MagicMock()

        with patch.object(issues, "current_user", return_value=current), patch.object(
            issues.issue_service, "list_issues", return_value=[]
        ) as list_mock, patch.object(
            issues.issue_service, "upvoted_issue_ids", return_value=set()
        ):
            response = issues.list_issues(
                auth=Mock(),
                db=db,
                status=IssueStatus.OPEN,
                category=IssueCategory.BUG,
                sort="upvotes",
                direction="asc",
            )

        self.assertEqual(response, [])
        list_mock.assert_called_once_with(
            db,
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            sort="upvotes",
            direction="asc",
        )

    def test_issue_detail_includes_current_user_upvoted(self) -> None:
        current = _user()
        reporter = _user()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=reporter.id,
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=1,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        issue.reporter = reporter
        issue.images = []

        with patch.object(issues, "current_user", return_value=current), patch.object(
            issues.issue_service, "get_issue", return_value=issue
        ), patch.object(issues.issue_service, "has_upvoted", return_value=True):
            response = issues.get_issue(issue.id, auth=Mock(), db=MagicMock())

        self.assertTrue(response.current_user_upvoted)

    def test_upvote_creates_row_increments_count_and_notifies_reporter(self) -> None:
        voter_id = uuid.uuid4()
        reporter_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=reporter_id,
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()
        db.scalar.return_value = 1

        with patch.object(
            issue_service, "get_issue", side_effect=[issue, issue]
        ), patch.object(
            issue_service.notification_service, "create_notification"
        ) as notify:
            result = issue_service.upvote_issue(db, issue.id, voter_id)

        self.assertIs(result, issue)
        self.assertIsInstance(db.add.call_args.args[0], IssueUpvote)
        db.flush.assert_called_once_with()
        self.assertTrue(db.execute.called)
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["user_id"], reporter_id)
        self.assertEqual(notify.call_args.kwargs["actor_id"], voter_id)
        self.assertEqual(
            notify.call_args.kwargs["type"], NotificationType.ISSUE_UPVOTED
        )
        self.assertEqual(notify.call_args.kwargs["metadata"]["upvote_count"], 1)

    def test_duplicate_upvote_is_idempotent_and_quiet(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=2,
        )
        db = Mock()
        db.flush.side_effect = IntegrityError("duplicate", {}, None)

        with patch.object(
            issue_service, "get_issue", side_effect=[issue, issue]
        ), patch.object(
            issue_service.notification_service, "create_notification"
        ) as notify:
            result = issue_service.upvote_issue(db, issue.id, user_id)

        self.assertIs(result, issue)
        self.assertEqual(issue.upvote_count, 2)
        db.rollback.assert_called_once_with()
        notify.assert_not_called()

    def test_own_issue_upvote_does_not_create_notification(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=user_id,
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()
        db.scalar.return_value = 1

        with patch.object(
            issue_service, "get_issue", side_effect=[issue, issue]
        ), patch.object(
            issue_service.notification_service, "create_notification"
        ) as notify:
            issue_service.upvote_issue(db, issue.id, user_id)

        db.commit.assert_called_once_with()
        notify.assert_not_called()

    def test_remove_upvote_decrements_count(self) -> None:
        issue = Issue(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=2,
        )
        db = Mock()
        result = Mock()
        result.rowcount = 1
        db.execute.return_value = result

        with patch.object(issue_service, "get_issue", side_effect=[issue, issue]):
            returned = issue_service.remove_upvote(db, issue.id, uuid.uuid4())

        self.assertIs(returned, issue)
        self.assertTrue(db.execute.called)
        db.commit.assert_called_once_with()

    def test_remove_missing_upvote_is_idempotent(self) -> None:
        issue = Issue(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="عنوان",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()
        result = Mock()
        result.rowcount = 0
        db.execute.return_value = result

        with patch.object(issue_service, "get_issue", side_effect=[issue, issue]):
            issue_service.remove_upvote(db, issue.id, uuid.uuid4())

        self.assertEqual(issue.upvote_count, 0)
        db.commit.assert_called_once_with()

    def test_issue_upvoted_is_in_app_only_email_policy(self) -> None:
        self.assertEqual(
            notification_email_policy.delivery_for_notification(
                NotificationType.ISSUE_UPVOTED
            ),
            notification_email_policy.NotificationDelivery.IN_APP_ONLY,
        )

    def test_models_are_available_to_alembic_metadata(self) -> None:
        self.assertIn("notifications", Base.metadata.tables)
        self.assertIn("issues", Base.metadata.tables)
        self.assertIn("issue_upvotes", Base.metadata.tables)
        self.assertIn("issue_images", Base.metadata.tables)


if __name__ == "__main__":
    unittest.main()
