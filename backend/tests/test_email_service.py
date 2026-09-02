from __future__ import annotations

import json
import unittest
from contextlib import ExitStack
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.services import email_service


class EmailServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        date_patch = patch.object(
            email_service,
            "format_date",
            return_value="١٩ ربيع الأول ١٤٤٨ هـ",
        )
        date_patch.start()
        self.addCleanup(date_patch.stop)

    def test_action_url_diagnostics_never_include_query_values(self) -> None:
        diagnostics = email_service._action_url_diagnostics(
            {
                "INVITATION_URL": (
                    "https://accounts.example/invitations/accept"
                    "?__clerk_ticket=secret-ticket&lang=ar"
                )
            }
        )

        self.assertEqual(
            diagnostics["INVITATION_URL"],
            {
                "scheme": "https",
                "host": "accounts.example",
                "path": "/invitations/accept",
                "query_keys": ["__clerk_ticket", "lang"],
            },
        )
        self.assertNotIn("secret-ticket", repr(diagnostics))

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

    @staticmethod
    def _payload(urlopen: Mock) -> dict[str, object]:
        request = urlopen.call_args.args[0]
        return json.loads(request.data.decode("utf-8"))

    def test_asset_base_url_is_derived_from_frontend_base_url(self) -> None:
        for frontend_url, expected in (
            ("https://albayan-journal.org/", "https://albayan-journal.org/email"),
            ("http://localhost:3000", "http://localhost:3000/email"),
        ):
            with self.subTest(frontend_url=frontend_url):
                with patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    frontend_url,
                ):
                    self.assertEqual(email_service._asset_base_url(), expected)

    def test_transport_sends_template_payload(self) -> None:
        response = Mock(status=200)
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                template_alias_or_id="welcome-template",
                variables={"USER_NAME": "أحمد"},
            )

        self.assertEqual(
            self._payload(urlopen)["template"],
            {"id": "welcome-template", "variables": {"USER_NAME": "أحمد"}},
        )

    def test_transport_sends_raw_html_payload(self) -> None:
        response = Mock(status=200)
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                subject="عنوان",
                html="<p>المحتوى</p>",
            )

        payload = self._payload(urlopen)
        self.assertEqual(payload["subject"], "عنوان")
        self.assertEqual(payload["html"], "<p>المحتوى</p>")
        self.assertNotIn("template", payload)

    def test_transport_rejects_template_and_raw_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "لا يمكن الجمع"):
            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                template_alias_or_id="welcome-template",
                subject="عنوان",
                html="<p>المحتوى</p>",
            )

    def test_transport_rejects_missing_content_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "يلزم تحديد قالب"):
            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
            )

    def test_transport_uses_configured_reply_to(self) -> None:
        response = Mock(status=200)
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                subject="عنوان",
                html="<p>المحتوى</p>",
            )

        self.assertEqual(
            self._payload(urlopen)["reply_to"],
            "Editorial <editor@example.com>",
        )

    def test_transport_identifies_backend_client(self) -> None:
        response = Mock(status=200)
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                subject="عنوان",
                html="<p>المحتوى</p>",
            )

        request = urlopen.call_args.args[0]
        headers = {name.lower(): value for name, value in request.header_items()}
        self.assertEqual(headers["user-agent"], "albayan-backend/1.0")
        self.assertEqual(headers["accept"], "application/json")

    def test_transport_sanitizes_resend_http_errors(self) -> None:
        provider_error = "provider-secret-response"
        error = HTTPError(
            "https://api.resend.com/emails",
            422,
            provider_error,
            hdrs=None,
            fp=BytesIO(provider_error.encode()),
        )
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.side_effect = error

            with self.assertLogs(email_service.logger, level="WARNING") as logs:
                with self.assertRaises(HTTPException) as raised:
                    email_service._send_resend_email(
                        to="author@example.com",
                        failure_detail="تعذّر الإرسال.",
                        subject="عنوان",
                        html="<p>المحتوى</p>",
                    )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "تعذّر الإرسال.")
        self.assertNotIn(provider_error, " ".join(logs.output))

    def test_welcome_email_sends_resend_template_payload(self) -> None:
        response = Mock()
        response.status = 200

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_welcome_template",
                    "welcome-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service.send_welcome_email(
                to="author@example.com",
                user_name="د. أحمد",
            )

        req = urlopen.call_args.args[0]
        payload = json.loads(req.data.decode("utf-8"))

        self.assertEqual(payload["from"], "Albayan <noreply@example.com>")
        self.assertEqual(
            payload["reply_to"],
            "مجلة البيان <support@albayan-journal.org>",
        )
        self.assertEqual(payload["to"], ["author@example.com"])
        self.assertEqual(
            payload["template"],
            {
                "id": "welcome-ar",
                "variables": {
                    "USER_NAME": "د. أحمد",
                    "LOGIN_URL": "https://albayan-journal.org/maktabi",
                    "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                    "SITE_URL": "https://albayan-journal.org",
                    "CONTACT_EMAIL": "support@albayan-journal.org",
                    "ASSET_BASE_URL": "https://albayan-journal.org/email",
                },
            },
        )
        self.assertNotIn("albayan@gmail.com", req.data.decode("utf-8"))
        self.assertEqual(req.method, "POST")
        self.assertEqual(
            req.headers["Authorization"],
            "Bearer re_test",
        )

    def test_app_invitation_email_sends_resend_template_payload(self) -> None:
        response = Mock(status=200)

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_app_invitation_template",
                    "app-invitation-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service.send_app_invitation_email(
                to="new-user@example.com",
                recipient_name="أحمد الزهراني",
                invitation_url="https://clerk.example/invitations/accept",
                expires_text="١٥ ربيع الأول ١٤٤٨ هـ",
            )

        payload = self._payload(urlopen)
        self.assertEqual(
            payload["template"],
            {
                "id": "app-invitation-ar",
                "variables": {
                    "INVITATION_URL": "https://clerk.example/invitations/accept",
                    "RECIPIENT_NAME": "أحمد الزهراني",
                    "RECIPIENT_EMAIL": "new-user@example.com",
                    "EXPIRES_TEXT": "١٥ ربيع الأول ١٤٤٨ هـ",
                    "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                    "SITE_URL": "https://albayan-journal.org",
                    "CONTACT_EMAIL": "support@albayan-journal.org",
                    "ASSET_BASE_URL": "https://albayan-journal.org/email",
                },
            },
        )

    def test_auth_verification_email_uses_idempotency_key(self) -> None:
        response = Mock(status=200)
        response.read.return_value = b'{"id":"email_123"}'

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_auth_verification_template",
                    "auth-verification-code-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            message_id = email_service.send_auth_verification_email(
                to="user@example.com",
                otp_code="123456",
                idempotency_key="clerk-email/email_1",
            )

        req = urlopen.call_args.args[0]
        payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(message_id, "email_123")
        self.assertEqual(req.headers["Idempotency-key"], "clerk-email/email_1")
        self.assertEqual(
            payload["template"],
            {
                "id": "auth-verification-code-ar",
                "variables": {
                    "OTP_CODE": "123456",
                    "RECIPIENT_EMAIL": "user@example.com",
                    "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                    "SITE_URL": "https://albayan-journal.org",
                    "CONTACT_EMAIL": "support@albayan-journal.org",
                    "ASSET_BASE_URL": "https://albayan-journal.org/email",
                },
            },
        )

    def test_password_reset_email_sends_resend_template_payload(self) -> None:
        response = Mock(status=200)

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_password_reset_template",
                    "password-reset-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service.send_password_reset_email(
                to="user@example.com",
                otp_code="654321",
            )

        payload = self._payload(urlopen)
        self.assertEqual(
            payload["template"],
            {
                "id": "password-reset-ar",
                "variables": {
                    "OTP_CODE": "654321",
                    "RECIPIENT_EMAIL": "user@example.com",
                    "DATE_TEXT": "١٩ ربيع الأول ١٤٤٨ هـ",
                    "SITE_URL": "https://albayan-journal.org",
                    "CONTACT_EMAIL": "support@albayan-journal.org",
                    "ASSET_BASE_URL": "https://albayan-journal.org/email",
                },
            },
        )

    def test_review_reminder_email_sends_declared_template_variables(self) -> None:
        response = Mock(status=200)

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
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
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service.send_review_reminder_email(
                to="reviewer@example.com",
                article_title="عنوان البحث",
                review_url="https://albayan-journal.org/maktabi/murajaati/1",
                due_text="٢٥ ربيع الأول ١٤٤٨ هـ",
                reminder_text="تبقى يوم واحد تقريبًا على موعد تسليم المراجعة.",
                idempotency_key="review-reminder/1/due-soon",
            )

        req = urlopen.call_args.args[0]
        payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(req.headers["Idempotency-key"], "review-reminder/1/due-soon")
        self.assertEqual(payload["template"]["id"], "review-reminder-ar")
        self.assertEqual(
            payload["template"]["variables"]["DUE_TEXT"],
            "٢٥ ربيع الأول ١٤٤٨ هـ",
        )

    def test_unread_digest_email_sends_declared_template_variables(self) -> None:
        response = Mock(status=200)

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_reply_to",
                    "مجلة البيان <support@albayan-journal.org>",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "resend_unread_notifications_digest_template",
                    "unread-notifications-digest-ar",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service.send_unread_notifications_digest_email(
                to="user@example.com",
                unread_count=6,
                notifications_url="https://albayan-journal.org/maktabi/isharat",
                idempotency_key="unread-digest/user/initial",
            )

        payload = self._payload(urlopen)
        self.assertEqual(payload["template"]["id"], "unread-notifications-digest-ar")
        self.assertEqual(payload["template"]["variables"]["UNREAD_COUNT"], 6)


if __name__ == "__main__":
    unittest.main()
