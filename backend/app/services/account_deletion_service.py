from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account_deletion_request import AccountDeletionRequest
from app.models.enums import AccountDeletionRequestStatus
from app.models.user import User

REVERIFICATION_PRESET = "strict"
REVERIFICATION_WINDOW_MINUTES = 10


class RequiresReverificationError(Exception):
    pass


def reverification_error_payload() -> dict[str, object]:
    return {
        "clerk_error": {
            "type": "forbidden",
            "reason": "reverification-error",
            "metadata": {"reverification": REVERIFICATION_PRESET},
        }
    }


def _has_recent_reverification(session_claims: dict[str, Any] | None) -> bool:
    fva = (session_claims or {}).get("fva")
    if not isinstance(fva, list) or len(fva) < 2:
        return False

    first_factor_age, second_factor_age = fva[0], fva[1]
    if not isinstance(first_factor_age, int):
        return False
    if first_factor_age < 0 or first_factor_age > REVERIFICATION_WINDOW_MINUTES:
        return False

    if second_factor_age == -1:
        return True
    return (
        isinstance(second_factor_age, int)
        and 0 <= second_factor_age <= REVERIFICATION_WINDOW_MINUTES
    )


def create_deletion_request(
    db: Session,
    *,
    user: User,
    session_claims: dict[str, Any] | None,
    reason: str | None,
) -> tuple[AccountDeletionRequest, bool]:
    if not _has_recent_reverification(session_claims):
        raise RequiresReverificationError()

    existing = db.scalar(
        select(AccountDeletionRequest)
        .where(AccountDeletionRequest.user_id == user.id)
        .where(AccountDeletionRequest.status == AccountDeletionRequestStatus.PENDING)
        .order_by(AccountDeletionRequest.requested_at.desc())
    )
    if existing:
        return existing, False

    request = AccountDeletionRequest(
        user_id=user.id,
        email_snapshot=user.email,
        reason=(reason or "").strip() or None,
        status=AccountDeletionRequestStatus.PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request, True


def list_deletion_requests(db: Session) -> list[AccountDeletionRequest]:
    return list(
        db.scalars(
            select(AccountDeletionRequest).order_by(
                AccountDeletionRequest.requested_at.desc()
            )
        )
    )


def update_deletion_request_status(
    db: Session,
    *,
    request_id,
    admin: User,
    status: AccountDeletionRequestStatus,
    resolution_note: str | None,
) -> AccountDeletionRequest:
    request = db.get(AccountDeletionRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="طلب حذف الحساب غير موجود.")

    request.status = status
    request.reviewed_by = admin.id
    request.reviewed_at = datetime.now(UTC)
    request.resolution_note = (resolution_note or "").strip() or None
    db.commit()
    db.refresh(request)
    return request
