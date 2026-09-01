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
from app.models.issue import Issue, IssueImage, IssueUpvote
from app.models.notification import Notification
from app.models.user import User
from app.routers import admin, issues, notifications
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
        db.flush.assert_called_once_with()
        db.commit.assert_not_called()

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

    def test_notification_page_returns_items_and_next_cursor(self) -> None:
        db = Mock()
        created = [
            datetime(2026, 1, 3, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
        ]
        rows = [
            Notification(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                type=NotificationType.SYSTEM,
                title=f"إشعار {index}",
                is_read=False,
                metadata_json={},
                created_at=value,
            )
            for index, value in enumerate(created)
        ]
        db.scalars.return_value.all.return_value = rows

        items, next_cursor = notification_service.list_notifications_page(
            db, uuid.uuid4(), limit=2
        )

        self.assertEqual(items, rows[:2])
        self.assertEqual(next_cursor, rows[1].created_at)

    def test_notification_page_route_uses_current_user(self) -> None:
        user = _user()
        db = Mock()

        with patch.object(
            notifications, "current_user", return_value=user
        ), patch.object(
            notifications.notification_service,
            "list_notifications_page",
            return_value=([], None),
        ) as list_mock:
            response = notifications.list_notifications_page(
                auth=Mock(), db=db, limit=20, before=None
            )

        self.assertEqual(response.items, [])
        self.assertIsNone(response.next_cursor)
        list_mock.assert_called_once_with(db, user.id, limit=20, before=None)


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

        with patch.object(
            issue_service, "_recent_issue_count", return_value=0
        ), patch.object(
            issue_service.workflow_notification_service,
            "admin_ids",
            return_value={uuid.uuid4()},
        ), patch.object(
            issue_service.workflow_notification_service,
            "notify_many",
        ) as notify:
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
        notify.assert_called_once()

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

    def test_issue_status_changed_is_digest_only_email_policy(self) -> None:
        self.assertEqual(
            notification_email_policy.delivery_for_notification(
                NotificationType.ISSUE_STATUS_CHANGED
            ),
            notification_email_policy.NotificationDelivery.IN_APP_ONLY,
        )

    def test_issue_image_upload_rejects_bad_inputs(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=user_id,
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()

        cases = [
            ("text/plain", b"image", 400),
            ("image/png", b"", 400),
            ("image/png", b"x" * (issue_service.MAX_ISSUE_IMAGE_BYTES + 1), 400),
        ]

        for content_type, body, status_code in cases:
            with self.subTest(content_type=content_type, size=len(body)):
                with patch.object(issue_service, "get_issue", return_value=issue):
                    with self.assertRaises(HTTPException) as raised:
                        issue_service.create_issue_image(
                            db,
                            issue_id=issue.id,
                            user_id=user_id,
                            body=body,
                            content_type=content_type,
                        )
                self.assertEqual(raised.exception.status_code, status_code)

    def test_fourth_issue_image_upload_is_rejected_before_s3_write(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=user_id,
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()
        db.scalar.return_value = 3

        with patch.object(issue_service, "get_issue", return_value=issue), patch.object(
            issue_service.s3, "put_bytes"
        ) as put_bytes:
            with self.assertRaises(HTTPException) as raised:
                issue_service.create_issue_image(
                    db,
                    issue_id=issue.id,
                    user_id=user_id,
                    body=b"image",
                    content_type="image/png",
                )

        self.assertEqual(raised.exception.status_code, 400)
        put_bytes.assert_not_called()

    def test_non_reporter_cannot_upload_or_delete_issue_images(self) -> None:
        issue = Issue(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        db = Mock()

        with patch.object(issue_service, "get_issue", return_value=issue):
            with self.assertRaises(HTTPException) as raised:
                issue_service.create_issue_image(
                    db,
                    issue_id=issue.id,
                    user_id=uuid.uuid4(),
                    body=b"image",
                    content_type="image/png",
                )
        self.assertEqual(raised.exception.status_code, 403)

        with patch.object(issue_service, "get_issue", return_value=issue):
            with self.assertRaises(HTTPException) as raised:
                issue_service.delete_issue_image(
                    db,
                    issue_id=issue.id,
                    image_id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                )
        self.assertEqual(raised.exception.status_code, 403)

    def test_issue_image_upload_creates_s3_key_and_db_row(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=user_id,
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        updated = Issue(
            id=issue.id,
            user_id=user_id,
            title=issue.title,
            description=issue.description,
            status=issue.status,
            category=issue.category,
            upvote_count=0,
        )
        db = Mock()
        db.scalar.side_effect = [0, None]

        with patch.object(
            issue_service, "get_issue", side_effect=[issue, updated]
        ), patch.object(issue_service.s3, "put_bytes") as put_bytes:
            result = issue_service.create_issue_image(
                db,
                issue_id=issue.id,
                user_id=user_id,
                body=b"image",
                content_type="image/png",
            )

        self.assertIs(result, updated)
        image = db.add.call_args.args[0]
        self.assertIsInstance(image, IssueImage)
        self.assertEqual(image.issue_id, issue.id)
        self.assertEqual(image.position, 0)
        self.assertTrue(
            image.s3_key.startswith(f"issues/{issue.id}/images/")
        )
        self.assertTrue(image.s3_key.endswith(".png"))
        put_bytes.assert_called_once()
        self.assertEqual(put_bytes.call_args.args[0], f"issues/{issue.id}/images")
        self.assertEqual(put_bytes.call_args.args[2], b"image")
        self.assertEqual(put_bytes.call_args.args[3], "image/png")
        db.commit.assert_called_once_with()

    def test_logged_in_viewer_can_resolve_issue_image(self) -> None:
        issue_id = uuid.uuid4()
        image = IssueImage(
            id=uuid.uuid4(),
            issue_id=issue_id,
            s3_key=f"issues/{issue_id}/images/test.png",
            position=0,
        )
        db = Mock()
        db.scalar.return_value = image

        with patch.object(issue_service, "get_issue") as get_issue_mock:
            result = issue_service.get_issue_image(db, issue_id, image.id)

        self.assertIs(result, image)
        get_issue_mock.assert_called_once_with(db, issue_id)

    def test_issue_image_delete_removes_row_and_attempts_s3_delete(self) -> None:
        user_id = uuid.uuid4()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=user_id,
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=0,
        )
        image = IssueImage(
            id=uuid.uuid4(),
            issue_id=issue.id,
            s3_key=f"issues/{issue.id}/images/test.png",
            position=0,
        )
        updated = Issue(
            id=issue.id,
            user_id=user_id,
            title=issue.title,
            description=issue.description,
            status=issue.status,
            category=issue.category,
            upvote_count=0,
        )
        db = Mock()
        db.scalar.return_value = image

        with patch.object(
            issue_service, "get_issue", side_effect=[issue, updated]
        ), patch.object(issue_service.s3, "delete_key") as delete_key:
            result = issue_service.delete_issue_image(
                db, issue.id, image.id, user_id
            )

        self.assertIs(result, updated)
        delete_key.assert_called_once_with(image.s3_key)
        db.delete.assert_called_once_with(image)
        db.commit.assert_called_once_with()


class AdminIssuePhase3Tests(unittest.TestCase):
    def _issue(self) -> Issue:
        reporter = _user()
        issue = Issue(
            id=uuid.uuid4(),
            user_id=reporter.id,
            title="بلاغ",
            description="وصف",
            status=IssueStatus.OPEN,
            category=IssueCategory.BUG,
            upvote_count=3,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        issue.reporter = reporter
        issue.images = []
        return issue

    def test_admin_issue_endpoints_use_admin_dependency(self) -> None:
        self.assertEqual(
            inspect.signature(admin.list_admin_issues).parameters["auth"].annotation,
            admin.AdminDep,
        )
        self.assertEqual(
            inspect.signature(admin.update_admin_issue_status).parameters[
                "auth"
            ].annotation,
            admin.AdminDep,
        )

    def test_regular_issue_router_has_no_status_mutation(self) -> None:
        route_paths = {getattr(route, "path", "") for route in issues.router.routes}
        self.assertNotIn("/api/v1/issues/{issue_id}/status", route_paths)

    def test_admin_list_passes_filters_and_sorting(self) -> None:
        admin_user = _user()
        db = MagicMock()

        with patch.object(admin, "_admin_user", return_value=admin_user), patch.object(
            admin.admin_issue_service, "list_issues", return_value=[]
        ) as list_mock:
            response = admin.list_admin_issues(
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

    def test_admin_issue_response_includes_reporter_email(self) -> None:
        issue = self._issue()

        response = admin._admin_issue_read(issue)

        self.assertEqual(response.reporter.email, issue.reporter.email)

    def test_same_status_patch_is_noop_without_notification(self) -> None:
        issue = self._issue()
        db = Mock()

        with patch.object(
            admin.admin_issue_service.issue_service,
            "get_issue",
            return_value=issue,
        ), patch.object(
            admin.admin_issue_service.notification_service, "create_notification"
        ) as notify:
            result = admin.admin_issue_service.update_issue_status(
                db,
                issue_id=issue.id,
                admin_id=uuid.uuid4(),
                status=IssueStatus.OPEN,
            )

        self.assertIs(result, issue)
        db.flush.assert_not_called()
        notify.assert_not_called()

    def test_status_patch_creates_reporter_notification_with_metadata(self) -> None:
        issue = self._issue()
        db = Mock()
        admin_id = uuid.uuid4()

        with patch.object(
            admin.admin_issue_service.issue_service,
            "get_issue",
            side_effect=[issue, issue],
        ), patch.object(
            admin.admin_issue_service.notification_service, "create_notification"
        ) as notify:
            result = admin.admin_issue_service.update_issue_status(
                db,
                issue_id=issue.id,
                admin_id=admin_id,
                status=IssueStatus.RESOLVED,
            )

        self.assertIs(result, issue)
        self.assertEqual(issue.status, IssueStatus.RESOLVED)
        db.flush.assert_called_once_with()
        notify.assert_called_once()
        kwargs = notify.call_args.kwargs
        self.assertEqual(kwargs["user_id"], issue.user_id)
        self.assertEqual(kwargs["actor_id"], admin_id)
        self.assertEqual(kwargs["type"], NotificationType.ISSUE_STATUS_CHANGED)
        self.assertEqual(
            kwargs["metadata"],
            {
                "issue_id": str(issue.id),
                "previous_status": "open",
                "next_status": "resolved",
            },
        )

    def test_models_are_available_to_alembic_metadata(self) -> None:
        self.assertIn("notifications", Base.metadata.tables)
        self.assertIn("issues", Base.metadata.tables)
        self.assertIn("issue_upvotes", Base.metadata.tables)
        self.assertIn("issue_images", Base.metadata.tables)


if __name__ == "__main__":
    unittest.main()
