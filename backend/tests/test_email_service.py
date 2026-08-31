from __future__ import annotations

import json
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from app.services import email_service


class EmailServiceTests(unittest.TestCase):
    def test_welcome_email_sends_resend_template_payload(self) -> None:
        response = Mock()
        response.status = 200

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <noreply@example.com>")
            )
            stack.enter_context(
                patch.object(email_service.settings, "email_reply_to", "Editor <editor@example.com>")
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
        self.assertEqual(payload["reply_to"], "Editor <editor@example.com>")
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

    def test_inline_email_sends_from_and_reply_to(self) -> None:
        response = Mock()
        response.status = 200

        with ExitStack() as stack:
            stack.enter_context(patch.object(email_service.settings, "resend_api_key", "re_test"))
            stack.enter_context(
                patch.object(email_service.settings, "email_from", "Albayan <mail@example.com>")
            )
            stack.enter_context(
                patch.object(email_service.settings, "email_reply_to", "Editor <editor@example.com>")
            )
            urlopen = stack.enter_context(
                patch.object(email_service.urllib.request, "urlopen")
            )
            urlopen.return_value.__enter__.return_value = response

            email_service._send_resend_email(
                to="reviewer@example.com",
                subject="Invitation",
                html="<p>Welcome</p>",
                failure_detail="Failed",
            )

        req = urlopen.call_args.args[0]
        payload = json.loads(req.data.decode("utf-8"))

        self.assertEqual(payload["from"], "Albayan <mail@example.com>")
        self.assertEqual(payload["reply_to"], "Editor <editor@example.com>")
        self.assertEqual(payload["to"], ["reviewer@example.com"])
        self.assertEqual(payload["subject"], "Invitation")
        self.assertEqual(payload["html"], "<p>Welcome</p>")


if __name__ == "__main__":
    unittest.main()
