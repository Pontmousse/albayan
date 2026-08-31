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
    def _configured_transport(self, stack: ExitStack):
        stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
        stack.enter_context(
            patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
        )
        return stack.enter_context(patch.object(email_service.urllib.request, "urlopen"))

    @staticmethod
    def _payload(urlopen: Mock) -> dict[str, object]:
        request = urlopen.call_args.args[0]
        return json.loads(request.data.decode("utf-8"))

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

    def test_transport_propagates_reply_to(self) -> None:
        response = Mock(status=200)
        with ExitStack() as stack:
            urlopen = self._configured_transport(stack)
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="author@example.com",
                failure_detail="تعذّر الإرسال.",
                subject="عنوان",
                html="<p>المحتوى</p>",
                reply_to="editor@example.com",
            )

        self.assertEqual(self._payload(urlopen)["reply_to"], "editor@example.com")

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
                    "resend_welcome_template_id",
                    "welcome-template-id",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "frontend_base_url",
                    "https://albayan-journal.org/",
                )
            )
            stack.enter_context(
                patch.object(
                    email_service.settings,
                    "email_asset_base_url",
                    "https://cdn.albayan-journal.org/email/",
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
        self.assertEqual(payload["to"], ["author@example.com"])
        self.assertEqual(
            payload["template"],
            {
                "id": "welcome-template-id",
                "variables": {
                    "USER_NAME": "د. أحمد",
                    "LOGIN_URL": "https://albayan-journal.org/maktabi",
                    "SITE_URL": "https://albayan-journal.org",
                    "ASSET_BASE_URL": "https://cdn.albayan-journal.org/email",
                },
            },
        )
        self.assertEqual(req.method, "POST")
        self.assertEqual(
            req.headers["Authorization"],
            "Bearer re_test",
        )


if __name__ == "__main__":
    unittest.main()
