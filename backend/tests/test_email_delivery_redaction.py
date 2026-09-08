import unittest

from app.services import email_delivery_service


class EmailDeliveryRedactionTests(unittest.TestCase):
    def test_safe_provider_message_redacts_email_and_full_url(self) -> None:
        safe = email_delivery_service._safe_text(
            "Rejected person@example.com; inspect https://provider.example/log?id=secret",
            1000,
        )

        self.assertEqual(
            safe,
            "Rejected [redacted-email]; inspect [redacted-url]",
        )
        self.assertNotIn("person@example.com", safe or "")
        self.assertNotIn("id=secret", safe or "")


if __name__ == "__main__":
    unittest.main()
