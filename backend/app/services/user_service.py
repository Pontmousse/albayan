import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import AuthContext
from app.models.user import User
from app.services import email_service

logger = logging.getLogger(__name__)


def get_or_create_user(db: Session, auth: AuthContext) -> User:
    if not auth.email:
        raise HTTPException(
            status_code=400,
            detail="يلزم وجود بريد إلكتروني للحساب.",
        )

    user = db.scalar(select(User).where(User.clerk_id == auth.clerk_id))
    if user:
        if user.email != auth.email:
            user.email = auth.email
            db.commit()
            db.refresh(user)
        return user

    user = User(
        clerk_id=auth.clerk_id,
        email=auth.email,
        full_name=auth.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        email_service.send_welcome_email(to=user.email, user_name=user.full_name)
    except Exception as exc:
        logger.warning("Welcome email failed for user %s: %s", user.id, exc)
    return user


def sync_clerk_name(clerk_id: str, full_name: str | None) -> None:
    if not full_name:
        return

    parts = full_name.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    from app.core.clerk import clerk_client

    clerk_client.users.update(
        user_id=clerk_id,
        first_name=first_name,
        last_name=last_name,
    )
