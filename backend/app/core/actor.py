"""Shared identity dependency for endpoints that are safe for humans or agents."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.clerk import get_auth_context
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import DB_UNAVAILABLE, current_user
from app.models.user import User
from app.services import agent_token_service


@dataclass(frozen=True)
class Actor:
    user_id: uuid.UUID
    clerk_id: str
    auth_method: Literal["human", "agent"]
    token_id: uuid.UUID | None = None


def _bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ").strip()
    return token or None


def get_current_actor(request: Request, db: Session = Depends(get_db)) -> Actor:
    # Use ActorDep only on endpoints explicitly classified as agent-safe.
    token = _bearer_token(request)
    if token and token.startswith("alb_"):
        if not settings.mcp_enabled:
            raise HTTPException(status_code=404, detail="غير موجود.")

        row, user = agent_token_service.authenticate_agent_token(db, token)
        return Actor(
            user_id=user.id,
            clerk_id=user.clerk_id,
            auth_method="agent",
            token_id=row.id,
        )

    auth = get_auth_context(request)
    user = current_user(auth, db)
    return Actor(user_id=user.id, clerk_id=user.clerk_id, auth_method="human")


def current_actor_user(actor: Actor, db: Session) -> User:
    try:
        user = db.get(User, actor.user_id)
    except OperationalError as exc:
        raise DB_UNAVAILABLE from exc

    if not user:
        raise HTTPException(status_code=401, detail="هوية المصادقة غير صالحة.")

    return user


ActorDep = Annotated[Actor, Depends(get_current_actor)]
