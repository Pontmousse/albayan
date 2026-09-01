from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.enums import (
    InvitationRole,
    NotificationType,
    ReviewerAssignmentStatus,
    ReviewStatus,
    VersionStatus,
)
from app.models.notification import Notification
from app.schemas.admin import InviteCreatePayload
from app.services import (
    admin_article_service,
    admin_user_service,
    article_service,
    notification_service,
    review_service,
)


class NotificationAtomicityTests(unittest.TestCase):
    def test_existing_event_key_returns_existing_notification(self) -> None:
        existing = Notification(
            user_id=uuid.uuid4(),
            type=NotificationType.SYSTEM,
            title="موجود",
            event_key="event:1",
        )
        db = Mock()
        db.scalar.return_value = existing

        result = notification_service.create_notification(
            db,
            user_id=existing.user_id,
            type=NotificationType.SYSTEM,
            title="جديد",
            event_key="event:1",
        )

        self.assertIs(result, existing)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_new_notification_flushes_without_committing(self) -> None:
        db = Mock()
        db.scalar.return_value = None

        result = notification_service.create_notification(
            db,
            user_id=uuid.uuid4(),
            type=NotificationType.ARTICLE_SUBMITTED,
            title="تم الاستلام",
            event_key="article:1:submitted:user:1",
        )

        db.add.assert_called_once_with(result)
        db.flush.assert_called_once_with()
        db.commit.assert_not_called()


class ReviewerDeadlineTests(unittest.TestCase):
    def test_reviewer_invitation_requires_due_at(self) -> None:
        with self.assertRaises(ValidationError):
            InviteCreatePayload(
                email="reviewer@example.com",
                role=InvitationRole.REVIEWER,
            )

        payload = InviteCreatePayload(
            email="editor@example.com",
            role=InvitationRole.EDITOR,
        )
        self.assertIsNone(payload.review_due_at)

    def test_direct_reviewer_assignment_rejects_missing_due_at(self) -> None:
        db = Mock()
        db.get.side_effect = [Mock(), Mock()]

        with self.assertRaises(HTTPException) as raised:
            admin_article_service.assign_reviewer(
                db,
                uuid.uuid4(),
                user_id=uuid.uuid4(),
                review_due_at=None,
            )

        self.assertEqual(raised.exception.status_code, 422)


class WorkflowDeliveryTests(unittest.TestCase):
    def test_submission_receipt_failure_does_not_skip_staff_email(self) -> None:
        article_id = uuid.uuid4()
        author_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        admin_id = uuid.uuid4()
        version = SimpleNamespace(
            status=VersionStatus.DRAFT,
            submitted_at=None,
            version_number=1,
        )
        article = SimpleNamespace(
            id=article_id,
            title="بحث",
            submitted_by=author_id,
        )
        submitter = SimpleNamespace(
            id=author_id,
            email="author@example.com",
            full_name="المؤلف",
        )
        editor = SimpleNamespace(
            id=editor_id,
            email="editor@example.com",
        )
        admin = SimpleNamespace(
            id=admin_id,
            email="admin@example.com",
        )
        result_author_ids = Mock()
        result_author_ids.all.return_value = [author_id]
        result_editor_ids = Mock()
        result_editor_ids.all.return_value = [editor_id]
        result_staff = Mock()
        result_staff.all.return_value = [editor, admin]
        db = Mock()
        db.scalars.side_effect = [
            result_author_ids,
            result_editor_ids,
            result_staff,
        ]
        db.get.return_value = submitter

        with patch.object(
            article_service, "current_version", return_value=version
        ), patch.object(
            article_service, "assert_document_metadata_matches"
        ), patch.object(
            article_service.workflow_notification_service,
            "admin_ids",
            return_value={admin_id},
        ), patch.object(
            article_service.workflow_notification_service, "notify_many"
        ), patch.object(
            article_service.email_service,
            "send_submission_received_email",
            side_effect=RuntimeError("mail down"),
        ), patch.object(
            article_service.email_service,
            "send_new_submission_alert_email",
        ) as staff_email:
            article_service.submit_article(db, article)

        self.assertEqual(staff_email.call_count, 2)

    def test_review_submission_uses_role_specific_links(self) -> None:
        article_id = uuid.uuid4()
        assignment_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        admin_id = uuid.uuid4()
        review = SimpleNamespace(
            id=uuid.uuid4(),
            status=ReviewStatus.DRAFT,
            recommendation="accept",
            submitted_at=None,
        )
        version = SimpleNamespace(id=uuid.uuid4())
        editor = SimpleNamespace(
            id=editor_id,
            email="editor@example.com",
            full_name="محرر",
        )
        admin = SimpleNamespace(
            id=admin_id,
            email="admin@example.com",
            full_name="مدير",
        )
        article = SimpleNamespace(
            id=article_id,
            title="بحث",
            editor_assignments=[SimpleNamespace(user_id=editor_id, user=editor)],
        )
        assignment = SimpleNamespace(
            id=assignment_id,
            article_id=article_id,
            user_id=reviewer_id,
            status=ReviewerAssignmentStatus.ACCEPTED,
        )
        reviewer = SimpleNamespace(
            id=reviewer_id,
            email="reviewer@example.com",
            full_name="مراجع",
        )
        admin_result = Mock()
        admin_result.all.return_value = [admin]
        db = Mock()
        db.scalar.return_value = article
        db.scalars.return_value = admin_result
        db.get.return_value = reviewer

        with patch.object(
            review_service.article_service, "current_version", return_value=version
        ), patch.object(
            review_service, "_review_for_current_version", return_value=review
        ), patch.object(
            review_service.workflow_notification_service,
            "admin_ids",
            return_value={admin_id},
        ), patch.object(
            review_service.workflow_notification_service, "notify_many"
        ) as notify, patch.object(
            review_service.email_service, "send_review_submitted_email"
        ) as send, patch.object(
            review_service.email_service.settings,
            "frontend_base_url",
            "http://localhost:3000",
        ):
            review_service.submit_review(db, assignment)

        links = {call.kwargs["link"] for call in notify.call_args_list}
        self.assertEqual(
            links,
            {
                f"/maktabi/tahriri/{article_id}",
                f"/admin/maqalat/{article_id}",
            },
        )
        report_urls = {call.kwargs["report_url"] for call in send.call_args_list}
        self.assertEqual(
            report_urls,
            {
                f"http://localhost:3000/maktabi/tahriri/{article_id}",
                f"http://localhost:3000/admin/maqalat/{article_id}",
            },
        )

    def test_admin_role_change_persists_and_notifies(self) -> None:
        user = SimpleNamespace(
            id=uuid.uuid4(),
            clerk_id="user_target",
            is_admin=False,
        )
        actor_id = uuid.uuid4()
        db = Mock()
        db.get.return_value = user

        with patch.object(
            admin_user_service.clerk_client.users, "update_metadata"
        ), patch.object(
            admin_user_service.workflow_notification_service, "notify_many"
        ) as notify:
            result = admin_user_service.set_admin_status(
                db,
                user.id,
                True,
                actor_id=actor_id,
            )

        self.assertIs(result, user)
        self.assertTrue(user.is_admin)
        self.assertEqual(notify.call_args.kwargs["actor_id"], actor_id)
        self.assertEqual(
            notify.call_args.kwargs["type"], NotificationType.ADMIN_ROLE_CHANGED
        )
        db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
