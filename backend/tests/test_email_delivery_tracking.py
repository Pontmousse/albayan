from __future__ import annotations

import unittest
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from svix.webhooks import WebhookVerificationError

from app.models.email_delivery import EmailDelivery, EmailDeliveryEvent
from app.services import email_delivery_service, email_service


class EmailDeliveryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        EmailDelivery.__table__.create(self.engine)
        EmailDeliveryEvent.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        session_patch = patch.object(
            email_delivery_service,
            "SessionLocal",
            self.Session,
        )
        session_patch.start()
        self.addCleanup(session_patch.stop)
        self.addCleanup(self.engine.dispose)

    def test_recorded_attempt_hashes_recipient_and_idempotency_key(self) -> None:
        row = email_delivery_service.record_accepted_email(
            provider_email_id="email_1",
            email_kind="auth_verification",
            recipient="User@Example.com",
            idempotency_key="clerk-email/secret-event-id",
        )

        self.assertEqual(row.provider_email_id, "email_1")
        self.assertEqual(row.latest_state, "accepted")
        self.assertEqual(len(row.recipient_hash), 64)
        self.assertNotIn("user@example.com", row.recipient_hash)
        self.assertIsNotNone(row.idempotency_key_hash)
        self.assertNotIn("secret-event-id", row.idempotency_key_hash or "")

    def test_resends_are_separate_attempts_and_latest_is_returned(self) -> None:
        now = datetime(2026, 9, 8, 10, 0, tzinfo=UTC)
        email_delivery_service.record_accepted_email(
            provider_email_id="email_first",
            email_kind="app_invitation",
            recipient="person@example.com",
            related_id="inv_1",
            accepted_at=now,
        )
        email_delivery_service.record_accepted_email(
            provider_email_id="email_second",
            email_kind="app_invitation",
            recipient="person@example.com",
            related_id="inv_1",
            accepted_at=now + timedelta(minutes=2),
        )

        latest = email_delivery_service.latest_delivery_for_context(
            email_kind="app_invitation",
            related_id="inv_1",
        )
        self.assertIsNotNone(latest)
        self.assertEqual(latest.provider_email_id, "email_second")

        with self.Session() as db:
            count = db.scalar(select(func.count()).select_from(EmailDelivery))
        self.assertEqual(count, 2)

    def test_webhook_is_idempotent_and_out_of_order_does_not_downgrade(self) -> None:
        accepted_at = datetime(2026, 9, 8, 10, 0, tzinfo=UTC)
        email_delivery_service.record_accepted_email(
            provider_email_id="email_2",
            email_kind="review_reminder",
            recipient="reviewer@example.com",
            accepted_at=accepted_at,
        )
        delivered_event = {
            "type": "email.delivered",
            "created_at": "2026-09-08T10:05:00Z",
            "data": {"email_id": "email_2"},
        }
        delayed_event = {
            "type": "email.delivery_delayed",
            "created_at": "2026-09-08T10:03:00Z",
            "data": {"email_id": "email_2"},
        }

        first = email_delivery_service.handle_resend_webhook(
            delivered_event,
            provider_event_id="msg_delivered",
        )
        duplicate = email_delivery_service.handle_resend_webhook(
            delivered_event,
            provider_event_id="msg_delivered",
        )
        email_delivery_service.handle_resend_webhook(
            delayed_event,
            provider_event_id="msg_delayed",
        )

        self.assertEqual(first["state"], "delivered")
        self.assertTrue(duplicate["duplicate"])
        with self.Session() as db:
            delivery = db.scalar(
                select(EmailDelivery).where(
                    EmailDelivery.provider_email_id == "email_2"
                )
            )
            event_count = db.scalar(
                select(func.count()).select_from(EmailDeliveryEvent)
            )
        self.assertEqual(delivery.latest_state, "delivered")
        self.assertEqual(event_count, 2)

    def test_webhook_before_acceptance_is_preserved_and_enriched(self) -> None:
        delivered_event = {
            "type": "email.delivered",
            "created_at": "2026-09-08T10:05:00Z",
            "data": {
                "email_id": "email_early",
                "to": ["person@example.com"],
            },
        }

        result = email_delivery_service.handle_resend_webhook(
            delivered_event,
            provider_event_id="msg_early_delivered",
        )
        self.assertTrue(result["matched"])

        with self.Session() as db:
            placeholder = db.scalar(
                select(EmailDelivery).where(
                    EmailDelivery.provider_email_id == "email_early"
                )
            )
        self.assertEqual(placeholder.latest_state, "delivered")
        self.assertEqual(placeholder.email_kind, "pending")
        self.assertNotIn("person@example.com", placeholder.recipient_hash)

        row = email_delivery_service.record_accepted_email(
            provider_email_id="email_early",
            email_kind="app_invitation",
            recipient="person@example.com",
            related_id="inv_early",
            accepted_at=datetime(2026, 9, 8, 10, 0, tzinfo=UTC),
        )

        self.assertEqual(row.email_kind, "app_invitation")
        self.assertEqual(row.related_id, "inv_early")
        self.assertEqual(row.latest_state, "delivered")
        with self.Session() as db:
            delivery_count = db.scalar(select(func.count()).select_from(EmailDelivery))
            event_count = db.scalar(
                select(func.count()).select_from(EmailDeliveryEvent)
            )
        self.assertEqual(delivery_count, 1)
        self.assertEqual(event_count, 1)

    def test_lifecycle_lookup_uses_row_lock(self) -> None:
        statement = email_delivery_service._locked_delivery_query("email_locked")
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.assertIn("FOR UPDATE", sql)

    def test_bounce_stores_only_allowlisted_diagnostics(self) -> None:
        email_delivery_service.record_accepted_email(
            provider_email_id="email_3",
            email_kind="app_invitation",
            recipient="person@example.com",
            related_id="inv_3",
        )
        event = {
            "type": "email.bounced",
            "created_at": "2026-09-08T10:05:00Z",
            "data": {
                "email_id": "email_3",
                "to": ["person@example.com"],
                "subject": "secret subject",
                "html": "<p>secret body</p>",
                "bounce": {
                    "type": "Permanent",
                    "subType": "Suppressed",
                    "message": "Mailbox rejected the message",
                },
            },
        }

        email_delivery_service.handle_resend_webhook(
            event,
            provider_event_id="msg_bounce",
        )

        with self.Session() as db:
            delivery = db.scalar(
                select(EmailDelivery).where(
                    EmailDelivery.provider_email_id == "email_3"
                )
            )
        self.assertEqual(delivery.latest_state, "bounced")
        self.assertEqual(delivery.failure_code, "Permanent:Suppressed")
        self.assertEqual(delivery.failure_message, "Mailbox rejected the message")
        stored = repr(
            (
                delivery.failure_code,
                delivery.failure_message,
                delivery.recipient_hash,
            )
        )
        self.assertNotIn("person@example.com", stored)
        self.assertNotIn("secret subject", stored)
        self.assertNotIn("secret body", stored)

    def test_invalid_webhook_signature_is_rejected(self) -> None:
        verifier = Mock()
        verifier.verify.side_effect = WebhookVerificationError("invalid")
        with patch.object(
            email_delivery_service.settings,
            "resend_webhook_signing_secret",
            "whsec_test",
        ), patch.object(
            email_delivery_service,
            "Webhook",
            return_value=verifier,
        ):
            with self.assertRaises(HTTPException) as raised:
                email_delivery_service.verify_resend_webhook(
                    payload=b"{}",
                    headers={
                        "svix-id": "msg_1",
                        "svix-timestamp": "1",
                        "svix-signature": "v1,bad",
                    },
                )
        self.assertEqual(raised.exception.status_code, 400)


class EmailTransportTrackingTests(unittest.TestCase):
    def _configured_transport(self, stack: ExitStack):
        stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
        stack.enter_context(
            patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
        )
        stack.enter_context(
            patch.object(
                email_service.settings,
                "email_reply_to",
                "Editorial <editor@example.com>",
            )
        )
        return stack.enter_context(patch.object(email_service.urllib.request, "urlopen"))

    def test_transport_records_acceptance_without_email_payload_secrets(self) -> None:
        response = Mock(status=200)
        response.read.return_value = b'{"id":"email_auth"}'
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_auth_verification_template",
                    "auth-template",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org",
                )
            )
            record = stack.enter_context(
                patch.object(
                    email_service.email_delivery_service,
                    "record_accepted_email",
                )
            )

            email_service.send_auth_verification_email(
                to="user@example.com",
                otp_code="123456",
                idempotency_key="clerk-email/event_1",
            )

        record.assert_called_once()
        kwargs = record.call_args.kwargs
        self.assertEqual(kwargs["provider_email_id"], "email_auth")
        self.assertEqual(kwargs["email_kind"], "auth_verification")
        self.assertEqual(kwargs["recipient"], "user@example.com")
        self.assertEqual(kwargs["idempotency_key"], "clerk-email/event_1")
        self.assertNotIn("variables", kwargs)
        self.assertNotIn("html", kwargs)
        self.assertNotIn("123456", repr(kwargs))

    def test_non_invitation_workflow_uses_shared_tracking_transport(self) -> None:
        response = Mock(status=200)
        response.read.return_value = b'{"id":"email_reminder"}'
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_review_reminder_template",
                    "review-reminder-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org",
                )
            )
            record = stack.enter_context(
                patch.object(
                    email_service.email_delivery_service,
                    "record_accepted_email",
                )
            )

            email_service.send_review_reminder_email(
                to="reviewer@example.com",
                article_title="بحث",
                review_url="https://albayan-journal.org/maktabi/murajaati/1",
                due_text="غداً",
                reminder_text="تذكير",
                idempotency_key="review-reminder/1/due-soon",
            )

        self.assertEqual(record.call_args.kwargs["email_kind"], "review_reminder")
        self.assertEqual(
            record.call_args.kwargs["provider_email_id"],
            "email_reminder",
        )


if __name__ == "__main__":
    unittest.main()
