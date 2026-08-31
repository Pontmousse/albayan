import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parseaddr
from typing import Any

from clerk_backend_api import models
from fastapi import HTTPException

from app.core.clerk import AuthContext, clerk_client
from app.core.config import settings
from app.core.dates import format_date
from app.services.email_service import send_app_invitation_email

logger = logging.getLogger(__name__)

_EMAIL_EXISTS_CODES = {
    "form_identifier_exists",
    "duplicate_record",
    "identifier_already_exists",
    "resource_already_exists",
}

_EMAIL_ADDRESS_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)


@dataclass(frozen=True)
class AppInvitation:
    id: str
    email: str
    status: str
    url: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None


def _normalize_email(email: str) -> str:
    _, address = parseaddr(email.strip())
    normalized = address.lower()
    if (
        not normalized
        or normalized != email.strip().lower()
        or not _EMAIL_ADDRESS_RE.fullmatch(normalized)
    ):
        raise HTTPException(status_code=422, detail="صيغة البريد الإلكتروني غير صحيحة.")
    return normalized


def _datetime_from_clerk_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, int):
        return None
    timestamp = value / 1000 if value > 10_000_000_000 else value
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _read_value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _invitation_read(invitation: Any) -> AppInvitation:
    created_at = _datetime_from_clerk_timestamp(_read_value(invitation, "created_at"))
    updated_at = _datetime_from_clerk_timestamp(_read_value(invitation, "updated_at"))
    status = _read_value(invitation, "status") or "pending"
    return AppInvitation(
        id=str(_read_value(invitation, "id") or ""),
        email=str(_read_value(invitation, "email_address") or ""),
        status=str(getattr(status, "value", status)),
        url=_read_value(invitation, "url"),
        created_at=created_at or datetime.now(UTC),
        updated_at=updated_at or created_at or datetime.now(UTC),
        expires_at=_datetime_from_clerk_timestamp(_read_value(invitation, "expires_at")),
    )


def _clerk_error_codes(exc: Exception) -> set[str]:
    data = getattr(exc, "data", None)
    errors = getattr(data, "errors", None) or []
    codes: set[str] = set()
    for error in errors:
        code = error.get("code") if isinstance(error, dict) else getattr(error, "code", None)
        if isinstance(code, str):
            codes.add(code)
    return codes


def _translate_clerk_error(exc: Exception, default_detail: str) -> HTTPException:
    status_code = getattr(exc, "status_code", None)
    codes = _clerk_error_codes(exc)
    if status_code == 409 or codes.intersection(_EMAIL_EXISTS_CODES):
        return HTTPException(
            status_code=409,
            detail="توجد دعوة معلّقة أو حساب مسجّل لهذا البريد.",
        )
    if status_code == 429:
        return HTTPException(
            status_code=429,
            detail="تم إرسال عدد كبير من الدعوات. حاول لاحقاً.",
        )
    if status_code in {400, 422}:
        return HTTPException(status_code=422, detail="تعذّر إنشاء الدعوة. تحقق من البريد.")
    if status_code in {401, 403}:
        return HTTPException(
            status_code=503,
            detail="صلاحيات Clerk غير مُهيّأة لإنشاء الدعوات.",
        )
    return HTTPException(status_code=502, detail=default_detail)


def _expires_text(invitation: AppInvitation) -> str | None:
    if invitation.expires_at is None:
        return None
    return format_date(invitation.expires_at)


def create_app_invitation(*, email: str, admin: AuthContext) -> AppInvitation:
    normalized_email = _normalize_email(email)
    redirect_url = f"{settings.frontend_base_url.rstrip('/')}/tasjil"

    try:
        invitation = clerk_client.invitations.create(
            request={
                "email_address": normalized_email,
                "redirect_url": redirect_url,
                "notify": False,
                "ignore_existing": False,
                "public_metadata": {
                    "source": "albayan-admin",
                    "invited_by_clerk_id": admin.clerk_id,
                },
            }
        )
    except models.ClerkErrors as exc:
        raise _translate_clerk_error(exc, "تعذّر إنشاء دعوة المستخدم في Clerk.") from exc
    except Exception as exc:
        logger.warning("Clerk app invitation creation failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="تعذّر إنشاء دعوة المستخدم في Clerk.",
        ) from exc

    app_invitation = _invitation_read(invitation)
    if not app_invitation.url:
        raise HTTPException(
            status_code=502,
            detail="أنشأ Clerk الدعوة دون رابط قبول صالح.",
        )

    send_app_invitation_email(
        to=app_invitation.email,
        invitation_url=app_invitation.url,
        expires_text=_expires_text(app_invitation),
    )
    return app_invitation


def list_app_invitations() -> list[AppInvitation]:
    try:
        rows = clerk_client.invitations.list(limit=50, order_by="-created_at")
    except Exception as exc:
        logger.warning("Clerk app invitation list failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="تعذّر تحميل دعوات المستخدمين من Clerk.",
        ) from exc

    return [_invitation_read(row) for row in rows]


def revoke_app_invitation(invitation_id: str) -> None:
    try:
        clerk_client.invitations.revoke(invitation_id=invitation_id)
    except models.ClerkErrors as exc:
        status_code = getattr(exc, "status_code", None)
        if status_code == 404:
            raise HTTPException(status_code=404, detail="الدعوة غير موجودة.") from exc
        if status_code in {400, 422}:
            raise HTTPException(
                status_code=409,
                detail="لا يمكن إلغاء هذه الدعوة.",
            ) from exc
        raise _translate_clerk_error(exc, "تعذّر إلغاء دعوة المستخدم.") from exc
    except Exception as exc:
        logger.warning("Clerk app invitation revoke failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="تعذّر إلغاء دعوة المستخدم.",
        ) from exc
