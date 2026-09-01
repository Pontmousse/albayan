import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import AuthContext
from app.core.clerk import clerk_client
from app.models.enums import UserGender
from app.models.user import User
from app.services import email_service

logger = logging.getLogger(__name__)

_GENDER_METADATA_KEY = "albayan_gender"
_INVITEE_NAME_METADATA_KEY = "albayan_invitee_name"


def _read_value(source: object, key: str) -> object | None:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _read_metadata(source: object, key: str) -> dict:
    value = _read_value(source, key)
    return value if isinstance(value, dict) else {}


def _gender_from_metadata(metadata: dict) -> UserGender | None:
    try:
        return UserGender(metadata.get(_GENDER_METADATA_KEY))
    except (TypeError, ValueError):
        return None


def _new_user_identity(clerk_id: str) -> tuple[UserGender | None, str | None]:
    """Read immutable onboarding data once when the local user is created."""
    try:
        clerk_user = clerk_client.users.get(user_id=clerk_id)
    except Exception as exc:
        logger.warning(
            "Could not read onboarding metadata for Clerk user %s (%s)",
            clerk_id,
            type(exc).__name__,
        )
        return None, None

    public_metadata = _read_metadata(clerk_user, "public_metadata")
    unsafe_metadata = _read_metadata(clerk_user, "unsafe_metadata")
    gender = _gender_from_metadata(public_metadata) or _gender_from_metadata(
        unsafe_metadata
    )
    invited_name = public_metadata.get(_INVITEE_NAME_METADATA_KEY)
    if not isinstance(invited_name, str) or not invited_name.strip():
        invited_name = None

    if gender and _gender_from_metadata(public_metadata) is None:
        try:
            clerk_client.users.update_metadata(
                user_id=clerk_id,
                public_metadata={_GENDER_METADATA_KEY: gender.value},
            )
        except Exception as exc:
            logger.warning(
                "Could not mirror onboarding metadata for Clerk user %s (%s)",
                clerk_id,
                type(exc).__name__,
            )

    return gender, invited_name.strip() if invited_name else None


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

    gender, invited_name = _new_user_identity(auth.clerk_id)
    user = User(
        clerk_id=auth.clerk_id,
        email=auth.email,
        full_name=auth.full_name or invited_name,
        gender=gender,
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
