from dataclasses import dataclass
from typing import Annotated, Any

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)


@dataclass
class AuthContext:
    clerk_id: str
    email: str | None
    full_name: str | None


def _read_value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _clean_email(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    email = value.strip()
    return email or None


def _email_from_address(address: Any) -> str | None:
    return _clean_email(
        _read_value(address, "email_address")
        or _read_value(address, "email")
        or _read_value(address, "identifier")
    )


def _email_from_payload(payload: dict[str, Any]) -> str | None:
    email = payload.get("email")
    if isinstance(email, list):
        email = email[0] if email else None

    direct_email = _clean_email(email or payload.get("email_address"))
    if direct_email:
        return direct_email

    for address in payload.get("email_addresses") or []:
        address_email = _email_from_address(address)
        if address_email:
            return address_email

    return None


def _primary_email_from_clerk_user(clerk_user: Any) -> str | None:
    primary_email_id = _read_value(clerk_user, "primary_email_address_id")
    email_addresses = _read_value(clerk_user, "email_addresses") or []

    if primary_email_id:
        for address in email_addresses:
            if _read_value(address, "id") == primary_email_id:
                return _email_from_address(address)

    for address in email_addresses:
        address_email = _email_from_address(address)
        if address_email:
            return address_email

    return _clean_email(_read_value(clerk_user, "email"))


def _resolve_email(clerk_id: str, payload: dict[str, Any]) -> str | None:
    payload_email = _email_from_payload(payload)
    if payload_email:
        return payload_email

    try:
        clerk_user = clerk_client.users.get(user_id=clerk_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="تعذر جلب بيانات الحساب من خدمة المصادقة حالياً.",
        ) from exc

    return _primary_email_from_clerk_user(clerk_user)


def get_auth_context(request: Request) -> AuthContext:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token.startswith("alb_"):
            raise HTTPException(
                status_code=401,
                detail="مفتاح الوكيل غير مسموح لهذا المسار.",
            )

    if not settings.clerk_secret_key:
        raise HTTPException(
            status_code=503,
            detail="المصادقة غير مُهيّأة على الخادم.",
        )

    state = clerk_client.authenticate_request(
        request,
        AuthenticateRequestOptions(
            authorized_parties=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "https://albayan-journal.org",
            ],
        ),
    )

    if not state.is_signed_in or not state.payload:
        raise HTTPException(status_code=401, detail="انتهت الجلسة، سجّل دخولك مجدداً.")

    payload = state.payload
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="رمز المصادقة غير صالح.")

    email = _resolve_email(clerk_id, payload)

    first_name = payload.get("first_name") or payload.get("given_name") or ""
    last_name = payload.get("last_name") or payload.get("family_name") or ""
    full_name = f"{first_name} {last_name}".strip() or None

    return AuthContext(clerk_id=clerk_id, email=email, full_name=full_name)


def _admin_role_from_metadata(public_metadata: Any) -> str | None:
    if not isinstance(public_metadata, dict):
        return None

    role = public_metadata.get("role")
    return role if isinstance(role, str) else None


def require_admin(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    try:
        clerk_user = clerk_client.users.get(user_id=auth.clerk_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="تعذر التحقق من صلاحيات المدير حالياً.",
        ) from exc

    role = _admin_role_from_metadata(getattr(clerk_user, "public_metadata", None))
    if role != "admin":
        raise HTTPException(status_code=403, detail="هذه الصفحة مخصّصة للمدير فقط.")

    return auth


AuthDep = Annotated[AuthContext, Depends(get_auth_context)]
AdminDep = Annotated[AuthContext, Depends(require_admin)]
DbDep = Annotated[Session, Depends(get_db)]
