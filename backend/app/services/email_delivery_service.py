from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.email_delivery import EmailDelivery, EmailDeliveryEvent

_EVENT_STATES = {
    "email.sent": "accepted",
    "email.delivered": "delivered",
    "email.delivery_delayed": "delayed",
    "email.bounced": "bounced",
    "email.failed": "failed",
    "email.complained": "complained",
    "email.suppressed": "suppressed",
}

_STATE_RANK = {
    "accepted": 0,
    "unknown": 0,
    "delayed": 1,
    "delivered": 2,
    "bounced": 3,
    "failed": 3,
    "suppressed": 3,
    "complained": 4,
}

_EMAIL_LIKE_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def recipient_hash(address: str) -> str:
    normalized = address.strip().lower().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _value_hash(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def record_accepted_email(
    *,
    provider_email_id: str | None,
    email_kind: str,
    recipient: str,
    event_scope: str | None = None,
    related_id: str | None = None,
    idempotency_key: str | None = None,
    accepted_at: datetime | None = None,
) -> EmailDelivery:
    provider_id = provider_email_id.strip() if provider_email_id else None
    accepted = accepted_at or datetime.now(UTC)

    with SessionLocal() as db:
        if provider_id:
            existing = db.scalar(
                select(EmailDelivery).where(
                    EmailDelivery.provider_email_id == provider_id
                )
            )
            if existing is not None:
                return existing

        delivery = EmailDelivery(
            provider_email_id=provider_id,
            email_kind=email_kind[:120],
            recipient_hash=recipient_hash(recipient),
            event_scope=event_scope[:120] if event_scope else None,
            related_id=related_id[:255] if related_id else None,
            idempotency_key_hash=_value_hash(idempotency_key),
            provider_accepted_at=accepted,
            latest_state="accepted",
        )
        db.add(delivery)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if provider_id:
                existing = db.scalar(
                    select(EmailDelivery).where(
                        EmailDelivery.provider_email_id == provider_id
                    )
                )
                if existing is not None:
                    return existing
            raise
        db.refresh(delivery)
        return delivery


def latest_delivery_for_context(*, email_kind: str, related_id: str) -> EmailDelivery | None:
    with SessionLocal() as db:
        return db.scalar(
            select(EmailDelivery)
            .where(
                EmailDelivery.email_kind == email_kind,
                EmailDelivery.related_id == related_id,
            )
            .order_by(
                EmailDelivery.created_at.desc(),
                EmailDelivery.provider_accepted_at.desc(),
            )
            .limit(1)
        )


def latest_deliveries_for_related_ids(
    *, email_kind: str, related_ids: list[str]
) -> dict[str, EmailDelivery]:
    if not related_ids:
        return {}
    with SessionLocal() as db:
        rows = db.scalars(
            select(EmailDelivery)
            .where(
                EmailDelivery.email_kind == email_kind,
                EmailDelivery.related_id.in_(related_ids),
            )
            .order_by(
                EmailDelivery.created_at.desc(),
                EmailDelivery.provider_accepted_at.desc(),
            )
        ).all()
    latest: dict[str, EmailDelivery] = {}
    for row in rows:
        if row.related_id and row.related_id not in latest:
            latest[row.related_id] = row
    return latest


def verify_resend_webhook(
    *, payload: bytes, headers: Mapping[str, str]
) -> dict[str, Any]:
    secret = settings.resend_webhook_signing_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Resend webhook signing is not configured.")
    try:
        event = Webhook(secret).verify(payload.decode("utf-8"), headers)
    except (WebhookVerificationError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Resend webhook signature.") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid Resend webhook payload.")
    return event


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_text(value: Any, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    value = _EMAIL_LIKE_RE.sub("[redacted-email]", value)
    value = _URL_RE.sub("[redacted-url]", value)
    return value[:limit] if value else None


def _diagnostics(data: dict[str, Any]) -> tuple[str | None, str | None]:
    for key in ("bounce", "failure", "error", "suppression"):
        detail = data.get(key)
        if not isinstance(detail, dict):
            continue
        code_parts = [
            _safe_text(detail.get(name), 70)
            for name in ("code", "type", "subType", "subtype", "reason")
        ]
        code = ":".join(part for part in code_parts if part) or None
        message = _safe_text(detail.get("message"), 1000)
        return code[:160] if code else None, message
    return None, None


def _should_apply_state(
    delivery: EmailDelivery, *, state: str, event_at: datetime | None
) -> bool:
    current_at = delivery.latest_provider_event_at
    if current_at is None:
        return True
    current_at = _normalize_datetime(current_at)
    if event_at is None:
        return _STATE_RANK.get(state, 0) >= _STATE_RANK.get(
            delivery.latest_state,
            0,
        )
    event_at = _normalize_datetime(event_at)
    if event_at > current_at:
        return True
    if event_at < current_at:
        return False
    return _STATE_RANK.get(state, 0) >= _STATE_RANK.get(delivery.latest_state, 0)


def handle_resend_webhook(
    event: dict[str, Any], *, provider_event_id: str | None
) -> dict[str, object]:
    event_type = event.get("type")
    if not isinstance(event_type, str) or event_type not in _EVENT_STATES:
        return {"ok": True, "ignored": True}

    data = event.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid Resend event payload.")
    provider_email_id = data.get("email_id")
    if not isinstance(provider_email_id, str) or not provider_email_id.strip():
        raise HTTPException(status_code=422, detail="Resend event is missing a valid email id.")
    provider_email_id = provider_email_id.strip()

    event_at = _parse_datetime(event.get("created_at")) or _parse_datetime(
        data.get("created_at")
    )
    event_id = provider_event_id.strip() if provider_event_id else ""
    if not event_id:
        fingerprint = (
            f"{event_type}|{provider_email_id}|"
            f"{event_at.isoformat() if event_at else ''}"
        )
        event_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()

    state = _EVENT_STATES[event_type]
    failure_code, failure_message = _diagnostics(data)

    with SessionLocal() as db:
        existing_event = db.scalar(
            select(EmailDeliveryEvent).where(
                EmailDeliveryEvent.provider_event_id == event_id
            )
        )
        if existing_event is not None:
            return {"ok": True, "duplicate": True}

        delivery = db.scalar(
            select(EmailDelivery).where(
                EmailDelivery.provider_email_id == provider_email_id
            )
        )
        if delivery is None:
            return {"ok": True, "matched": False}

        db.add(
            EmailDeliveryEvent(
                delivery_id=delivery.id,
                provider_event_id=event_id[:255],
                event_type=event_type,
                state=state,
                provider_event_at=event_at,
            )
        )

        if _should_apply_state(delivery, state=state, event_at=event_at):
            delivery.latest_state = state
            delivery.latest_provider_event = event_type
            delivery.latest_provider_event_at = event_at or datetime.now(UTC)
            if state in {"bounced", "failed", "complained", "suppressed"}:
                delivery.failure_code = failure_code
                delivery.failure_message = failure_message
            elif state == "delivered":
                delivery.failure_code = None
                delivery.failure_message = None

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return {"ok": True, "duplicate": True}

    return {"ok": True, "matched": True, "state": state}
