from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account_deletion_request import AccountDeletionRequest
from app.models.enums import AccountDeletionRequestStatus, NotificationType
from app.models.user import User
from app.services import workflow_notification_service

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
    db.flush()
    workflow_notification_service.notify_many(
        db,
        user_ids=workflow_notification_service.admin_ids(db),
        type=NotificationType.ACCOUNT_DELETION_REQUESTED,
        title="طلب حذف حساب جديد",
        body=f"أرسل {user.full_name or user.email} طلبًا لحذف الحساب.",
        link="/admin/mustakhdimin",
        actor_id=user.id,
        event_scope=f"account-deletion:{request.id}:requested",
        metadata={"request_id": str(request.id), "user_id": str(user.id)},
    )
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
    if request.status == status:
        return request

    request.status = status
    request.reviewed_by = admin.id
    request.reviewed_at = datetime.now(UTC)
    request.resolution_note = (resolution_note or "").strip() or None
    status_label = {
        AccountDeletionRequestStatus.PENDING: "بانتظار المراجعة",
        AccountDeletionRequestStatus.APPROVED: "مقبول",
        AccountDeletionRequestStatus.REJECTED: "مرفوض",
        AccountDeletionRequestStatus.COMPLETED: "مكتمل",
    }[status]
    workflow_notification_service.notify_many(
        db,
        user_ids={request.user_id},
        type=NotificationType.ACCOUNT_DELETION_STATUS_CHANGED,
        title="تغيّرت حالة طلب حذف الحساب",
        body=f"أصبحت حالة طلب حذف حسابك: {status_label}.",
        link="/al-idayat",
        actor_id=admin.id,
        event_scope=f"account-deletion:{request.id}:status:{status.value}",
        metadata={"request_id": str(request.id), "status": status.value},
    )
    db.commit()
    db.refresh(request)
    return request
