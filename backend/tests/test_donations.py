from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

from fastapi import HTTPException
from pydantic import SecretStr

from app.core.config import settings
from app.models.base import Base
from app.models.donation import DonationEmailReceipt
from app.services import donation_service


class DonationModelTests(unittest.TestCase):
    def test_only_durable_donation_state_is_email_receipt(self) -> None:
        receipts = Base.metadata.tables["donation_email_receipts"]
        self.assertIs(receipts, DonationEmailReceipt.__table__)
        self.assertIn("stripe_checkout_session_id", receipts.c)
        self.assertIn("email_sent_at", receipts.c)
        self.assertNotIn("amount_minor", receipts.c)
        self.assertNotIn("currency", receipts.c)
        self.assertNotIn("donor_email", receipts.c)

    def test_minimizing_migration_removes_payment_mirror_tables(self) -> None:
        path = Path(__file__).parents[1] / "alembic/versions/020_minimize_donation_state.py"
        spec = importlib.util.spec_from_file_location("migration_020", path)
        assert spec and spec.loader
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        fake_op = MagicMock()

        with patch.object(migration, "op", fake_op):
            migration.upgrade()

        dropped = [call.args[0] for call in fake_op.drop_table.call_args_list]
        self.assertEqual(dropped, ["stripe_webhook_events", "donations"])
        created = [call.args[0] for call in fake_op.create_table.call_args_list]
        self.assertEqual(created, ["donation_email_receipts"])


class DonationServiceTests(unittest.TestCase):
    def _stripe_patches(self):
        return (
            patch.object(settings, "stripe_secret_key", SecretStr("sk_test_example")),
            patch.object(
                settings,
                "stripe_webhook_signing_secret",
                SecretStr("whsec_example"),
            ),
            patch.object(settings, "donation_currency", "cad"),
            patch.object(settings, "donation_min_amount_minor", 500),
            patch.object(settings, "donation_max_amount_minor", 500000),
            patch.object(settings, "donation_minor_unit_divisor", 100),
        )

    def test_public_config_and_amount_bounds(self) -> None:
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            config = donation_service.public_config()
            self.assertEqual(config.currency, "cad")
            self.assertEqual(config.preset_amounts_minor, [1000, 2500, 5000])
            with self.assertRaises(HTTPException) as too_small:
                donation_service._validate_amount(499)
            self.assertEqual(too_small.exception.status_code, 422)
            with self.assertRaises(HTTPException) as too_large:
                donation_service._validate_amount(500001)
            self.assertEqual(too_large.exception.status_code, 422)

    def test_create_checkout_session_enables_adaptive_pricing_without_db(self) -> None:
        session = SimpleNamespace(id="cs_test_123", client_secret="cs_test_secret_123")
        client = MagicMock()
        client.v1.checkout.sessions.create.return_value = session
        patches = self._stripe_patches()

        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            donation_service, "_stripe_client", return_value=client
        ), patch.object(settings, "frontend_base_url", "https://albayan-journal.org"):
            result = donation_service.create_checkout_session(2500)

        self.assertEqual(result.session_id, "cs_test_123")
        params = client.v1.checkout.sessions.create.call_args.kwargs["params"]
        self.assertEqual(params["ui_mode"], "elements")
        self.assertEqual(params["mode"], "payment")
        self.assertEqual(params["adaptive_pricing"], {"enabled": True})
        self.assertNotIn("allowed_payment_method_types", params)
        self.assertEqual(params["line_items"][0]["price_data"]["unit_amount"], 2500)
        self.assertEqual(params["line_items"][0]["price_data"]["currency"], "cad")
        self.assertEqual(params["metadata"]["albayan_flow"], "albayan_donation")
        self.assertNotIn("albayan_donation_id", params["metadata"])

    def test_checkout_failure_logs_stripe_diagnostics_without_secrets(self) -> None:
        class StripeRequestError(Exception):
            code = "parameter_invalid"
            param = "allowed_payment_method_types"
            request_id = "req_test_managed_payments"

        client = MagicMock()
        client.v1.checkout.sessions.create.side_effect = StripeRequestError(
            "allowed_payment_method_types cannot be used with Managed Payments"
        )
        patches = self._stripe_patches()

        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            donation_service, "_stripe_client", return_value=client
        ), patch.object(settings, "frontend_base_url", "https://albayan-journal.org"), self.assertLogs(
            donation_service.logger, level="WARNING"
        ) as logs:
            with self.assertRaises(HTTPException) as error:
                donation_service.create_checkout_session(2500)

        self.assertEqual(error.exception.status_code, 502)
        output = "\n".join(logs.output)
        self.assertIn("StripeRequestError", output)
        self.assertIn("parameter_invalid", output)
        self.assertIn("allowed_payment_method_types", output)
        self.assertIn("req_test_managed_payments", output)
        self.assertIn("Managed Payments", output)
        self.assertNotIn("sk_test_example", output)
        self.assertNotIn("whsec_example", output)

    def test_session_status_reads_stripe_and_prefers_presentment_currency(self) -> None:
        session = {
            "id": "cs_test_paid",
            "status": "complete",
            "payment_status": "paid",
            "amount_total": 2500,
            "currency": "cad",
            "presentment_details": {
                "presentment_amount": 1800,
                "presentment_currency": "usd",
            },
            "metadata": {"albayan_flow": "albayan_donation"},
        }
        client = MagicMock()
        client.v1.checkout.sessions.retrieve.return_value = session
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            donation_service, "_stripe_client", return_value=client
        ):
            result = donation_service.session_status("cs_test_paid")

        self.assertEqual(result.status, "paid")
        self.assertEqual(result.amount_minor, 1800)
        self.assertEqual(result.currency, "usd")
        client.v1.checkout.sessions.retrieve.assert_called_once_with("cs_test_paid")

    def test_invalid_signature_is_mapped_without_provider_detail(self) -> None:
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            donation_service.stripe.Webhook,
            "construct_event",
            side_effect=ValueError("provider internals"),
        ):
            with self.assertRaises(HTTPException) as error:
                donation_service.verify_stripe_webhook(b"{}", "bad")
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "طلب غير صالح.")

    def test_paid_webhook_stores_only_email_deduplication_receipt(self) -> None:
        db = MagicMock()
        db.get.side_effect = [None, None]
        event = {
            "id": "evt_paid_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_paid",
                    "amount_total": 2500,
                    "currency": "cad",
                    "payment_status": "paid",
                    "customer_details": {"email": "donor@example.com"},
                    "metadata": {"albayan_flow": "albayan_donation"},
                }
            },
        }
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            type(settings), "email_enabled", new_callable=PropertyMock, return_value=True
        ), patch.object(
            donation_service.donation_email_service,
            "send_donation_received_email",
        ) as send:
            result = donation_service.handle_stripe_webhook(db, event)

        self.assertEqual(result, {"received": True, "email_sent": True})
        stored = db.add.call_args.args[0]
        self.assertIsInstance(stored, DonationEmailReceipt)
        self.assertEqual(stored.stripe_checkout_session_id, "cs_test_paid")
        self.assertIsNotNone(stored.email_sent_at)
        send.assert_called_once_with(
            to="donor@example.com",
            amount_text="25.00 CAD",
            donation_reference="cs_test_paid",
            idempotency_key=f"donation-received/cs_test_paid",
        )

    def test_paid_webhook_does_not_resend_after_durable_email_receipt(self) -> None:
        db = MagicMock()
        db.get.return_value = DonationEmailReceipt(
            stripe_checkout_session_id="cs_test_paid",
            email_sent_at=datetime.now(UTC),
        )
        event = {
            "type": "checkout.session.async_payment_succeeded",
            "data": {
                "object": {
                    "id": "cs_test_paid",
                    "payment_status": "paid",
                    "customer_details": {"email": "donor@example.com"},
                    "metadata": {"albayan_flow": "albayan_donation"},
                }
            },
        }
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            type(settings), "email_enabled", new_callable=PropertyMock, return_value=True
        ), patch.object(
            donation_service.donation_email_service,
            "send_donation_received_email",
        ) as send:
            result = donation_service.handle_stripe_webhook(db, event)
        self.assertEqual(result, {"received": True, "email_sent": False})
        send.assert_not_called()

    def test_status_rejects_untrusted_session_id(self) -> None:
        with self.assertRaises(HTTPException) as error:
            donation_service.session_status("../../etc/passwd")
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
