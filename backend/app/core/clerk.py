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


def get_auth_context(request: Request) -> AuthContext:
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

    email = payload.get("email")
    if isinstance(email, list):
        email = email[0] if email else None

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
