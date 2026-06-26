from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import AuthContext
from app.models.user import User


def get_or_create_user(db: Session, auth: AuthContext) -> User:
    user = db.scalar(select(User).where(User.clerk_id == auth.clerk_id))
    if user:
        if auth.email and user.email != auth.email:
            user.email = auth.email
            db.commit()
            db.refresh(user)
        return user

    user = User(
        clerk_id=auth.clerk_id,
        email=auth.email or f"{auth.clerk_id}@unknown.local",
        full_name=auth.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
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
