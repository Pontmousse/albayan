import hashlib
import secrets
import uuid
from base64 import urlsafe_b64encode

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent_token import AgentToken

ALLOWED_AGENT_SCOPES: frozenset[str] = frozenset(
    {
        "profile:read",
        "articles:read",
        "articles:session:write",
        "reviews:read",
        "reviews:draft:write",
        "editor:read",
    }
)

DEFAULT_AGENT_SCOPES: list[str] = [
    "profile:read",
    "articles:read",
    "articles:session:write",
]

MAX_ACTIVE_AGENT_TOKENS = 5

_NOT_FOUND = HTTPException(status_code=404, detail="المفتاح غير موجود.")
_LIMIT_REACHED = HTTPException(
    status_code=409,
    detail="بلغت الحد الأقصى لعدد مفاتيح الوكيل (٥). احذف مفتاحاً قديماً أولاً.",
)
_INVALID_SCOPES = HTTPException(
    status_code=400,
    detail="نطاق الصلاحيات غير صالح.",
)


def normalize_scopes(scopes: list[str]) -> list[str]:
    if not scopes:
        raise _INVALID_SCOPES
    unique = []
    seen: set[str] = set()
    for scope in scopes:
        if scope not in ALLOWED_AGENT_SCOPES:
            raise _INVALID_SCOPES
        if scope not in seen:
            seen.add(scope)
            unique.append(scope)
    return unique


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_agent_token() -> tuple[str, str]:
    raw = secrets.token_bytes(32)
    token = f"alb_{urlsafe_b64encode(raw).decode('ascii').rstrip('=')}"
    return token, _hash_token(token)


def _active_token_count(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count())
        .select_from(AgentToken)
        .where(
            AgentToken.user_id == user_id,
            AgentToken.revoked_at.is_(None),
        )
    ) or 0


def list_agent_tokens(db: Session, user_id: uuid.UUID) -> list[AgentToken]:
    return list(
        db.scalars(
            select(AgentToken)
            .where(
                AgentToken.user_id == user_id,
                AgentToken.revoked_at.is_(None),
            )
            .order_by(AgentToken.created_at.desc())
        ).all()
    )


def create_agent_token(
    db: Session,
    user_id: uuid.UUID,
    label: str,
    scopes: list[str],
) -> tuple[AgentToken, str]:
    if _active_token_count(db, user_id) >= MAX_ACTIVE_AGENT_TOKENS:
        raise _LIMIT_REACHED

    plaintext, token_hash = generate_agent_token()
    row = AgentToken(
        user_id=user_id,
        token_hash=token_hash,
        label=label,
        scopes=scopes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, plaintext


def get_agent_token_for_user(
    db: Session,
    user_id: uuid.UUID,
    token_id: uuid.UUID,
) -> AgentToken:
    row = db.scalar(
        select(AgentToken).where(
            AgentToken.id == token_id,
            AgentToken.user_id == user_id,
            AgentToken.revoked_at.is_(None),
        )
    )
    if not row:
        raise _NOT_FOUND
    return row


def update_agent_token_label(
    db: Session,
    user_id: uuid.UUID,
    token_id: uuid.UUID,
    label: str,
) -> AgentToken:
    row = get_agent_token_for_user(db, user_id, token_id)
    row.label = label
    db.commit()
    db.refresh(row)
    return row


def delete_agent_token(
    db: Session,
    user_id: uuid.UUID,
    token_id: uuid.UUID,
) -> None:
    row = get_agent_token_for_user(db, user_id, token_id)
    db.delete(row)
    db.commit()


def authenticate_agent_token(
    db: Session,
    plaintext: str,
) -> tuple[AgentToken, "User"]:
    from app.models.user import User

    if not plaintext.startswith("alb_"):
        raise HTTPException(status_code=401, detail="مفتاح الوكيل غير صالح.")

    token_hash = _hash_token(plaintext)
    row = db.scalar(
        select(AgentToken).where(
            AgentToken.token_hash == token_hash,
            AgentToken.revoked_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=401, detail="مفتاح الوكيل غير صالح.")

    if row.expires_at is not None:
        from datetime import UTC, datetime

        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="انتهت صلاحية مفتاح الوكيل.")

    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="مفتاح الوكيل غير صالح.")

    from datetime import UTC, datetime

    row.last_used_at = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return row, user
