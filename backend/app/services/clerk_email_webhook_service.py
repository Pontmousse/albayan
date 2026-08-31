import logging
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.services import email_service

logger = logging.getLogger(__name__)

VERIFICATION_CODE_SLUGS = {
    "verification_code",
    "email_verification_code",
    "sign_up_verification_code",
    "signup_verification_code",
}

PASSWORD_RESET_SLUGS = {
    "reset_password",
    "reset_password_code",
    "password_reset",
    "password_reset_code",
}


def verify_clerk_webhook(
    *,
    payload: bytes,
    headers: Mapping[str, str],
) -> dict[str, Any]:
    if not settings.clerk_webhook_signing_secret:
        raise HTTPException(
            status_code=503,
            detail="توقيع Clerk Webhook غير مُهيّأ على الخادم.",
        )

    try:
        event = Webhook(settings.clerk_webhook_signing_secret).verify(
            payload.decode("utf-8"),
            headers,
        )
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail="توقيع Clerk Webhook غير صالح.") from exc

    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="حمولة Clerk Webhook غير صالحة.")
    return event


def _email_data(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = event.get("type")
    if event_type not in {"email.created", "emails.created"}:
        return None

    data = event.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="حمولة بريد Clerk غير صالحة.")
    return data


def _otp_code(data: dict[str, Any]) -> str:
    metadata = data.get("data")
    otp_code = metadata.get("otp_code") if isinstance(metadata, dict) else None
    if not isinstance(otp_code, str) or not otp_code.strip():
        raise HTTPException(
            status_code=422,
            detail="بريد Clerk المدعوم لا يحتوي على رمز تحقق صالح.",
        )
    return otp_code.strip()


def _recipient(data: dict[str, Any]) -> str:
    recipient = data.get("to_email_address")
    if not isinstance(recipient, str) or not recipient.strip():
        raise HTTPException(
            status_code=422,
            detail="بريد Clerk المدعوم لا يحتوي على مستلم صالح.",
        )
    return recipient.strip()


def _idempotency_key(data: dict[str, Any]) -> str | None:
    email_id = data.get("id")
    if not isinstance(email_id, str) or not email_id.strip():
        return None
    return f"clerk-email/{email_id.strip()}"


def handle_clerk_webhook(event: dict[str, Any]) -> dict[str, object]:
    data = _email_data(event)
    if data is None:
        return {"ok": True, "ignored": True}

    if data.get("delivered_by_clerk") is True:
        return {"ok": True, "ignored": True}

    slug = data.get("slug")
    if not isinstance(slug, str):
        return {"ok": True, "ignored": True}

    normalized_slug = slug.strip()
    recipient = _recipient(data)
    otp_code = _otp_code(data)
    idempotency_key = _idempotency_key(data)

    if normalized_slug in VERIFICATION_CODE_SLUGS:
        message_id = email_service.send_auth_verification_email(
            to=recipient,
            otp_code=otp_code,
            idempotency_key=idempotency_key,
        )
        return {"ok": True, "message_id": message_id}

    if normalized_slug in PASSWORD_RESET_SLUGS:
        message_id = email_service.send_password_reset_email(
            to=recipient,
            otp_code=otp_code,
            idempotency_key=idempotency_key,
        )
        return {"ok": True, "message_id": message_id}

    logger.info("Ignoring unsupported Clerk email slug %s", normalized_slug)
    return {"ok": True, "ignored": True}
