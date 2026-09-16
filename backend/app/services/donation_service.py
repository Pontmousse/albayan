from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.donation import Donation, StripeWebhookEvent
from app.schemas.donation import (
    DonationCheckoutResponse,
    DonationConfigResponse,
    DonationSessionStatusResponse,
)
from app.services import donation_email_service

logger = logging.getLogger(__name__)

DONATION_FLOW_METADATA = "albayan_donation"
DEFAULT_PRESET_AMOUNTS_MINOR = (1000, 2500, 5000)
SUPPORTED_WEBHOOK_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.async_payment_failed",
    "checkout.session.expired",
}


def _secret_value(value: Any) -> str:
    if hasattr(value, "get_secret_value"):
        return value.get_secret_value()
    return str(value or "")


def _read(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _require_stripe() -> None:
    if not settings.stripe_enabled:
        raise HTTPException(
            status_code=503,
            detail="خدمة المساهمة غير متاحة مؤقتاً.",
        )


def _stripe_client() -> stripe.StripeClient:
    _require_stripe()
    return stripe.StripeClient(
        _secret_value(settings.stripe_secret_key),
        stripe_version="2026-08-26.dahlia",
    )


def public_config() -> DonationConfigResponse:
    _require_stripe()
    presets = [
        amount
        for amount in DEFAULT_PRESET_AMOUNTS_MINOR
        if settings.donation_min_amount_minor
        <= amount
        <= settings.donation_max_amount_minor
    ]
    return DonationConfigResponse(
        currency=settings.donation_currency,
        min_amount_minor=settings.donation_min_amount_minor,
        max_amount_minor=settings.donation_max_amount_minor,
        minor_unit_divisor=settings.donation_minor_unit_divisor,
        preset_amounts_minor=presets,
    )


def _validate_amount(amount_minor: int) -> None:
    if amount_minor < settings.donation_min_amount_minor:
        raise HTTPException(
            status_code=422,
            detail="مقدار المساهمة أقل من الحد المسموح.",
        )
    if amount_minor > settings.donation_max_amount_minor:
        raise HTTPException(
            status_code=422,
            detail="مقدار المساهمة أكبر من الحد المسموح.",
        )


def create_checkout_session(
    db: Session,
    amount_minor: int,
) -> DonationCheckoutResponse:
    _require_stripe()
    _validate_amount(amount_minor)

    donation_id = uuid.uuid4()
    metadata = {
        "albayan_flow": DONATION_FLOW_METADATA,
        "albayan_donation_id": str(donation_id),
    }
    return_url = (
        f"{settings.frontend_base_url.rstrip('/')}/daam-al-bayan/tamam"
        "?session_id={CHECKOUT_SESSION_ID}"
    )

    try:
        session = _stripe_client().v1.checkout.sessions.create(
            params={
                "ui_mode": "elements",
                "mode": "payment",
                "return_url": return_url,
                "allowed_payment_method_types": ["card"],
                "billing_address_collection": "auto",
                "line_items": [
                    {
                        "price_data": {
                            "currency": settings.donation_currency,
                            "unit_amount": amount_minor,
                            "product_data": {
                                "name": "دعم مجلة البيان",
                                "description": (
                                    "مساهمة اختيارية لدعم استمرار المشروع العلمي المفتوح."
                                ),
                            },
                        },
                        "quantity": 1,
                    }
                ],
                "metadata": metadata,
                "payment_intent_data": {"metadata": metadata},
            }
        )
    except Exception as exc:
        logger.warning(
            "Stripe Checkout Session creation failed error=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="تعذّر بدء عملية المساهمة. حاول مجدداً.",
        ) from exc

    session_id = _read(session, "id")
    client_secret = _read(session, "client_secret")
    if not isinstance(session_id, str) or not isinstance(client_secret, str):
        logger.error("Stripe Checkout Session missing id/client_secret")
        raise HTTPException(
            status_code=502,
            detail="تعذّر بدء عملية المساهمة. حاول مجدداً.",
        )

    donation = Donation(
        id=donation_id,
        stripe_checkout_session_id=session_id,
        amount_minor=amount_minor,
        currency=settings.donation_currency,
        status="pending",
    )
    db.add(donation)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(
            "Donation persistence failed after Checkout Session creation error=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="تعذّر حفظ عملية المساهمة. حاول مجدداً.",
        ) from exc

    return DonationCheckoutResponse(
        client_secret=client_secret,
        session_id=session_id,
        amount_minor=amount_minor,
        currency=settings.donation_currency,
    )


def session_status(db: Session, session_id: str) -> DonationSessionStatusResponse:
    if not session_id.startswith("cs_") or len(session_id) > 255:
        raise HTTPException(status_code=404, detail="تعذّر العثور على عملية المساهمة.")

    donation = db.scalar(
        select(Donation).where(Donation.stripe_checkout_session_id == session_id)
    )
    if donation is None:
        raise HTTPException(status_code=404, detail="تعذّر العثور على عملية المساهمة.")

    return DonationSessionStatusResponse(
        session_id=donation.stripe_checkout_session_id,
        status=donation.status,
        amount_minor=donation.amount_minor,
        currency=donation.currency,
    )


def verify_stripe_webhook(payload: bytes, signature: str) -> Any:
    _require_stripe()
    if not signature:
        raise HTTPException(status_code=400, detail="طلب غير صالح.")

    try:
        return stripe.Webhook.construct_event(
            payload,
            signature,
            _secret_value(settings.stripe_webhook_signing_secret),
        )
    except Exception as exc:
        logger.warning("Stripe webhook rejected error=%s", type(exc).__name__)
        raise HTTPException(status_code=400, detail="طلب غير صالح.") from exc


def _session_metadata(session: Any) -> dict[str, Any]:
    metadata = _read(session, "metadata", {})
    return metadata if isinstance(metadata, dict) else dict(metadata or {})


def _payment_intent_id(session: Any) -> str | None:
    payment_intent = _read(session, "payment_intent")
    if isinstance(payment_intent, str):
        return payment_intent
    value = _read(payment_intent, "id")
    return value if isinstance(value, str) else None


def _customer_email(session: Any) -> str | None:
    details = _read(session, "customer_details")
    email = _read(details, "email") or _read(session, "customer_email")
    if not isinstance(email, str):
        return None
    email = email.strip().lower()
    return email[:320] if email else None


def _donation_for_session(db: Session, session: Any) -> Donation | None:
    session_id = _read(session, "id")
    if not isinstance(session_id, str):
        return None

    donation = db.scalar(
        select(Donation).where(Donation.stripe_checkout_session_id == session_id)
    )
    if donation is not None:
        return donation

    metadata = _session_metadata(session)
    if metadata.get("albayan_flow") != DONATION_FLOW_METADATA:
        return None

    donation_id_raw = metadata.get("albayan_donation_id")
    try:
        donation_id = uuid.UUID(str(donation_id_raw))
    except (TypeError, ValueError, AttributeError):
        return None

    amount_minor = _read(session, "amount_total")
    currency = _read(session, "currency")
    if not isinstance(amount_minor, int) or amount_minor <= 0:
        return None
    if not isinstance(currency, str) or len(currency) != 3:
        return None

    donation = Donation(
        id=donation_id,
        stripe_checkout_session_id=session_id,
        amount_minor=amount_minor,
        currency=currency.lower(),
        status="pending",
    )
    db.add(donation)
    return donation


def _format_amount(donation: Donation) -> str:
    divisor = settings.donation_minor_unit_divisor
    major = donation.amount_minor / divisor
    decimals = 0 if divisor == 1 else len(str(divisor)) - 1
    return f"{major:.{decimals}f} {donation.currency.upper()}"


def _maybe_send_confirmation(db: Session, donation: Donation | None) -> None:
    if (
        donation is None
        or donation.status != "paid"
        or donation.confirmation_email_sent_at is not None
        or not donation.donor_email
        or not settings.email_enabled
    ):
        return

    try:
        donation_email_service.send_donation_received_email(
            to=donation.donor_email,
            amount_text=_format_amount(donation),
            donation_reference=str(donation.id),
            idempotency_key=f"donation-received/{donation.stripe_checkout_session_id}",
        )
    except Exception as exc:
        logger.warning(
            "Donation confirmation email failed donation_id=%s error=%s",
            donation.id,
            type(exc).__name__,
        )
        return

    donation.confirmation_email_sent_at = datetime.now(UTC)
    db.commit()


def handle_stripe_webhook(db: Session, event: Any) -> dict[str, object]:
    event_id = _read(event, "id")
    event_type = _read(event, "type")
    if not isinstance(event_id, str) or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="طلب غير صالح.")

    data = _read(event, "data", {})
    session = _read(data, "object")
    existing = db.get(StripeWebhookEvent, event_id)
    if existing is not None:
        donation = _donation_for_session(db, session)
        _maybe_send_confirmation(db, donation)
        return {"received": True, "duplicate": True}

    receipt = StripeWebhookEvent(event_id=event_id, event_type=event_type)
    db.add(receipt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        donation = _donation_for_session(db, session)
        _maybe_send_confirmation(db, donation)
        return {"received": True, "duplicate": True}

    if event_type not in SUPPORTED_WEBHOOK_EVENTS:
        db.commit()
        return {"received": True, "ignored": True}

    metadata = _session_metadata(session)
    if metadata.get("albayan_flow") != DONATION_FLOW_METADATA:
        db.commit()
        return {"received": True, "ignored": True}

    donation = _donation_for_session(db, session)
    if donation is None:
        logger.warning("Stripe donation webhook could not resolve donation event=%s", event_id)
        db.commit()
        return {"received": True, "ignored": True}

    donation.stripe_payment_intent_id = _payment_intent_id(session)
    donor_email = _customer_email(session)
    if donor_email:
        donation.donor_email = donor_email

    payment_status = _read(session, "payment_status")
    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    } and payment_status == "paid":
        donation.status = "paid"
    elif event_type == "checkout.session.async_payment_failed":
        donation.status = "failed"
    elif event_type == "checkout.session.expired" and donation.status != "paid":
        donation.status = "expired"

    db.commit()
    _maybe_send_confirmation(db, donation)
    return {"received": True}
