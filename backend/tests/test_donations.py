from __future__ import annotations

import importlib.util
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

from fastapi import HTTPException
from pydantic import SecretStr

from app.core.config import settings
from app.models.base import Base
from app.models.donation import Donation, StripeWebhookEvent
from app.services import donation_service


class DonationModelTests(unittest.TestCase):
    def test_model_metadata_has_privacy_minimal_tables_and_constraints(self) -> None:
        donations = Base.metadata.tables["donations"]
        self.assertIs(donations, Donation.__table__)
        self.assertNotIn("card_number", donations.c)
        self.assertNotIn("cvc", donations.c)
        self.assertIn("stripe_checkout_session_id", donations.c)
        self.assertIn("confirmation_email_sent_at", donations.c)
        constraints = {constraint.name for constraint in donations.constraints}
        self.assertIn("ck_donations_amount_positive", constraints)
        self.assertIn("ck_donations_status", constraints)
        self.assertIs(Base.metadata.tables["stripe_webhook_events"], StripeWebhookEvent.__table__)

    def test_migration_creates_and_drops_both_tables(self) -> None:
        path = Path(__file__).parents[1] / "alembic/versions/019_add_donations.py"
        spec = importlib.util.spec_from_file_location("migration_019", path)
        assert spec and spec.loader
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        fake_op = MagicMock()

        with patch.object(migration, "op", fake_op):
            migration.upgrade()
            migration.downgrade()

        created = [call.args[0] for call in fake_op.create_table.call_args_list]
        self.assertEqual(created, ["donations", "stripe_webhook_events"])
        dropped = [call.args[0] for call in fake_op.drop_table.call_args_list]
        self.assertEqual(dropped, ["stripe_webhook_events", "donations"])


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

    def test_create_checkout_session_uses_elements_and_server_owned_amount(self) -> None:
        db = MagicMock()
        session = SimpleNamespace(id="cs_test_123", client_secret="cs_test_secret_123")
        client = MagicMock()
        client.v1.checkout.sessions.create.return_value = session
        patches = self._stripe_patches()

        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            donation_service, "_stripe_client", return_value=client
        ), patch.object(settings, "frontend_base_url", "https://albayan-journal.org"):
            result = donation_service.create_checkout_session(db, 2500)

        self.assertEqual(result.session_id, "cs_test_123")
        self.assertEqual(result.amount_minor, 2500)
        params = client.v1.checkout.sessions.create.call_args.kwargs["params"]
        self.assertEqual(params["ui_mode"], "elements")
        self.assertEqual(params["mode"], "payment")
        self.assertEqual(params["allowed_payment_method_types"], ["card"])
        self.assertEqual(params["line_items"][0]["price_data"]["unit_amount"], 2500)
        self.assertEqual(params["line_items"][0]["price_data"]["currency"], "cad")
        self.assertIn("{CHECKOUT_SESSION_ID}", params["return_url"])
        self.assertNotIn("success_url", params)
        self.assertNotIn("cancel_url", params)
        db.add.assert_called_once()
        stored = db.add.call_args.args[0]
        self.assertIsInstance(stored, Donation)
        self.assertEqual(stored.amount_minor, 2500)
        db.commit.assert_called_once_with()

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
        self.assertNotIn("provider", error.exception.detail)

    def test_paid_webhook_is_idempotent_and_sends_one_confirmation(self) -> None:
        db = MagicMock()
        donation = Donation(
            id=uuid.uuid4(),
            stripe_checkout_session_id="cs_test_paid",
            amount_minor=2500,
            currency="cad",
            status="pending",
        )
        db.get.return_value = None
        db.scalar.return_value = donation
        event = {
            "id": "evt_paid_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_paid",
                    "amount_total": 2500,
                    "currency": "cad",
                    "payment_status": "paid",
                    "payment_intent": "pi_123",
                    "customer_details": {"email": "donor@example.com"},
                    "metadata": {
                        "albayan_flow": "albayan_donation",
                        "albayan_donation_id": str(donation.id),
                    },
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
            first = donation_service.handle_stripe_webhook(db, event)

        self.assertEqual(first, {"received": True})
        self.assertEqual(donation.status, "paid")
        self.assertEqual(donation.stripe_payment_intent_id, "pi_123")
        self.assertEqual(donation.donor_email, "donor@example.com")
        self.assertIsNotNone(donation.confirmation_email_sent_at)
        send.assert_called_once()

        db.get.return_value = StripeWebhookEvent(
            event_id="evt_paid_1",
            event_type="checkout.session.completed",
        )
        patches = self._stripe_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch.object(
            type(settings), "email_enabled", new_callable=PropertyMock, return_value=True
        ), patch.object(
            donation_service.donation_email_service,
            "send_donation_received_email",
        ) as send_duplicate:
            duplicate = donation_service.handle_stripe_webhook(db, event)
        self.assertEqual(duplicate, {"received": True, "duplicate": True})
        send_duplicate.assert_not_called()

    def test_non_donation_stripe_event_is_ignored(self) -> None:
        db = MagicMock()
        db.get.return_value = None
        event = {
            "id": "evt_other",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_other",
                    "metadata": {"albayan_flow": "something_else"},
                }
            },
        }
        result = donation_service.handle_stripe_webhook(db, event)
        self.assertEqual(result, {"received": True, "ignored": True})
        db.commit.assert_called_once_with()
        db.scalar.assert_not_called()

    def test_status_rejects_untrusted_session_id(self) -> None:
        with self.assertRaises(HTTPException) as error:
            donation_service.session_status(MagicMock(), "../../etc/passwd")
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()