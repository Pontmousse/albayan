"""مصادقة الوكلاء — API Key (alb_) و OAuth Clerk (JWT)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.clerk import get_auth_context
from app.core.config import settings
from app.core.deps import current_user
from app.services import agent_token_service

MCP_OAUTH_SCOPES: frozenset[str] = frozenset({"profile:read", "articles:read"})


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: uuid.UUID
    clerk_id: str
    scopes: frozenset[str]
    auth_method: Literal["api_key", "oauth"]
    token_id: uuid.UUID | None = None


def _require_agent_auth_enabled() -> None:
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="يلزم مصادقة.")
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="يلزم مصادقة.")
    return token


def resolve_agent_principal(request: Request, db: Session) -> AuthPrincipal:
    """يحلّ هوية الوكيل من alb_ أو Clerk JWT (OAuth). يتطلب DEV_MODE=true."""
    _require_agent_auth_enabled()
    token = _extract_bearer_token(request)

    if token.startswith("alb_"):
        row, user = agent_token_service.authenticate_agent_token(db, token)
        return AuthPrincipal(
            user_id=user.id,
            clerk_id=user.clerk_id,
            scopes=frozenset(row.scopes),
            auth_method="api_key",
            token_id=row.id,
        )

    auth = get_auth_context(request)
    user = current_user(auth, db)
    return AuthPrincipal(
        user_id=user.id,
        clerk_id=user.clerk_id,
        scopes=MCP_OAUTH_SCOPES,
        auth_method="oauth",
    )


def require_scope(principal: AuthPrincipal, scope: str) -> None:
    if scope not in principal.scopes:
        raise HTTPException(status_code=403, detail="صلاحية غير كافية.")
