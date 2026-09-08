from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from app.core.config import settings

_TOKEN_VERSION = 1
_SIGNING_CONTEXT = b"albayan-email-action-handoff-v1\0"


@dataclass(frozen=True)
class HandoffClaims:
    kind: str
    subject: str
    expires_at: datetime


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except Exception as exc:
        raise HTTPException(status_code=404, detail="رابط الدعوة غير صالح.") from exc


def _sign(payload: bytes) -> bytes:
    secret = settings.clerk_secret_key.strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="خدمة روابط الدعوات غير مُهيّأة على الخادم.",
        )
    return hmac.new(
        secret.encode("utf-8"),
        _SIGNING_CONTEXT + payload,
        hashlib.sha256,
    ).digest()


def create_handoff_token(
    *,
    kind: str,
    subject: str,
    expires_at: datetime,
) -> str:
    if not kind or not subject:
        raise ValueError("kind and subject are required")
    expiry = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    payload = json.dumps(
        {
            "v": _TOKEN_VERSION,
            "k": kind,
            "s": subject,
            "exp": int(expiry.astimezone(UTC).timestamp()),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"{_encode(payload)}.{_encode(_sign(payload))}"


def verify_handoff_token(
    token: str,
    *,
    expected_kind: str,
    now: datetime | None = None,
) -> HandoffClaims:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="رابط الدعوة غير صالح.") from exc

    payload = _decode(payload_part)
    signature = _decode(signature_part)
    if not hmac.compare_digest(signature, _sign(payload)):
        raise HTTPException(status_code=404, detail="رابط الدعوة غير صالح.")

    try:
        values: Any = json.loads(payload.decode("utf-8"))
        version = values["v"]
        kind = values["k"]
        subject = values["s"]
        exp = values["exp"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=404, detail="رابط الدعوة غير صالح.") from exc

    if (
        version != _TOKEN_VERSION
        or kind != expected_kind
        or not isinstance(subject, str)
        or not subject
        or not isinstance(exp, int)
    ):
        raise HTTPException(status_code=404, detail="رابط الدعوة غير صالح.")

    expires_at = datetime.fromtimestamp(exp, tz=UTC)
    current = now or datetime.now(UTC)
    if current >= expires_at:
        raise HTTPException(status_code=410, detail="انتهت صلاحية رابط الدعوة.")

    return HandoffClaims(
        kind=kind,
        subject=subject,
        expires_at=expires_at,
    )
