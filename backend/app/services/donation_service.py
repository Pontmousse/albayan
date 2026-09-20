from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import stripe
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.donation import DonationEmailReceipt
from app.schemas.donation import (
    DonationCheckoutResponse,
    DonationConfigResponse,
    DonationSessionStatusResponse,
)
from app.services import donation_email_service

logger = logging.getLogger(__name__)

DONATION_FLOW_METADATA = "albayan_donation"
DEFAULT_PRESET_AMOUNTS_MINOR = (1000, 2500, 5000)
PAID_WEBHOOK_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
}
ZERO_DECIMAL_CURRENCIES = {
    "bif",
    "clp",
    "djf",
    "gnf",
    "jpy",
    "kmf",
    "krw",
    "mga",
    "pyg",
    "rwf",
    "ugx",
    "vnd",
    "vuv",
    "xaf",
    "xof",
    "xpf",
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


def create_checkout_session(amount_minor: int) -> DonationCheckoutResponse:
    _require_stripe()
    _validate_amount(amount_minor)

    metadata = {"albayan_flow": DONATION_FLOW_METADATA}
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
                "managed_payments": {"enabled": False},
                "adaptive_pricing": {"enabled": True},
                "excluded_payment_method_types": ["klarna"],
                "billing_address_collection": "auto",
                "line_items": [
                    {
                        "price_data": {
                            "currency": settings.donation_currency,
                            "unit_amount": amount_minor,
                            "product_data": {
                                "name": "دعم مجلة البيان",
                                "description": "مساهمة لدعم استمرار المشروع العلمي المفتوح.",
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
        stripe_message = str(exc).replace("\n", " ")[:500]
        logger.warning(
            "Stripe Checkout Session creation failed error=%s code=%s param=%s request_id=%s message=%s",
            type(exc).__name__,
            getattr(exc, "code", None),
            getattr(exc, "param", None),
            getattr(exc, "request_id", None),
            stripe_message,
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

    return DonationCheckoutResponse(
        client_secret=client_secret,
        session_id=session_id,
        amount_minor=amount_minor,
        currency=settings.donation_currency,
    )


def _session_metadata(session: Any) -> dict[str, Any]:
    metadata = _read(session, "metadata", {})
    if isinstance(metadata, dict):
        return metadata
    if metadata is None:
        return {}

    to_dict = getattr(metadata, "to_dict", None)
    if callable(to_dict):
        plain_metadata = to_dict()
        if isinstance(plain_metadata, dict):
            return plain_metadata

    logger.warning("Unexpected Stripe session metadata type=%s", type(metadata).__name__)
    return {}


def _validate_donation_session(session: Any) -> None:
    if _session_metadata(session).get("albayan_flow") != DONATION_FLOW_METADATA:
        raise HTTPException(status_code=404, detail="تعذّر العثور على عملية المساهمة.")


def _presented_amount_and_currency(session: Any) -> tuple[int, str]:
    presentment = _read(session, "presentment_details", {})
    amount = _read(presentment, "presentment_amount")
    currency = _read(presentment, "presentment_currency")
    if isinstance(amount, int) and amount >= 0 and isinstance(currency, str):
        return amount, currency.lower()

    amount = _read(session, "amount_total")
    currency = _read(session, "currency")
    if not isinstance(amount, int) or amount < 0 or not isinstance(currency, str):
        raise HTTPException(status_code=502, detail="تعذّر التحقق من عملية المساهمة.")
    return amount, currency.lower()


def session_status(session_id: str) -> DonationSessionStatusResponse:
    if not session_id.startswith("cs_") or len(session_id) > 255:
        raise HTTPException(status_code=404, detail="تعذّر العثور على عملية المساهمة.")

    try:
        session = _stripe_client().v1.checkout.sessions.retrieve(session_id)
    except Exception as exc:
        logger.warning(
            "Stripe Checkout Session retrieval failed error=%s",
            type(exc).__name__,
        )
        raise HTTPException(status_code=404, detail="تعذّر العثور على عملية المساهمة.") from exc

    _validate_donation_session(session)
    amount_minor, currency = _presented_amount_and_currency(session)
    payment_status = _read(session, "payment_status")
    checkout_status = _read(session, "status")

    if payment_status == "paid":
        status = "paid"
    elif checkout_status == "expired":
        status = "expired"
    elif checkout_status == "complete":
        status = "failed"
    else:
        status = "pending"

    return DonationSessionStatusResponse(
        session_id=session_id,
        status=status,
        amount_minor=amount_minor,
        currency=currency,
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


def _customer_email(session: Any) -> str | None:
    details = _read(session, "customer_details")
    email = _read(details, "email") or _read(session, "customer_email")
    if not isinstance(email, str):
        return None
    email = email.strip().lower()
    return email[:320] if email else None


def _format_amount(session: Any) -> str:
    amount_minor, currency = _presented_amount_and_currency(session)
    divisor = 1 if currency in ZERO_DECIMAL_CURRENCIES else 100
    major = amount_minor / divisor
    decimals = 0 if divisor == 1 else 2
    return f"{major:.{decimals}f} {currency.upper()}"


def _send_confirmation_once(db: Session, session: Any) -> bool:
    session_id = _read(session, "id")
    donor_email = _customer_email(session)
    if (
        not isinstance(session_id, str)
        or not donor_email
        or not settings.email_enabled
    ):
        return False

    receipt = db.get(DonationEmailReceipt, session_id)
    if receipt is not None and receipt.email_sent_at is not None:
        return False

    if receipt is None:
        receipt = DonationEmailReceipt(stripe_checkout_session_id=session_id)
        db.add(receipt)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            receipt = db.get(DonationEmailReceipt, session_id)
            if receipt is not None and receipt.email_sent_at is not None:
                return False

    try:
        donation_email_service.send_donation_received_email(
            to=donor_email,
            amount_text=_format_amount(session),
            donation_reference=session_id,
            idempotency_key=f"donation-received/{session_id}",
        )
    except Exception as exc:
        logger.warning(
            "Donation confirmation email failed session=%s error=%s",
            session_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="تعذّر معالجة إشعار الدفع.",
        ) from exc

    receipt = db.get(DonationEmailReceipt, session_id) or receipt
    if receipt is not None:
        receipt.email_sent_at = datetime.now(UTC)
        db.commit()
    return True


def handle_stripe_webhook(db: Session, event: Any) -> dict[str, object]:
    event_type = _read(event, "type")
    if not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="طلب غير صالح.")

    data = _read(event, "data", {})
    session = _read(data, "object")

    if event_type not in PAID_WEBHOOK_EVENTS:
        return {"received": True, "ignored": True}
    if _session_metadata(session).get("albayan_flow") != DONATION_FLOW_METADATA:
        return {"received": True, "ignored": True}
    if _read(session, "payment_status") != "paid":
        return {"received": True, "ignored": True}

    sent = _send_confirmation_once(db, session)
    return {"received": True, "email_sent": sent}
