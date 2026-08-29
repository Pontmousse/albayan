import uuid

from fastapi import APIRouter, Query

from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.models.notification import Notification
from app.schemas.notification import (
    MarkAllReadResult,
    NotificationActorRead,
    NotificationRead,
    UnreadCountRead,
)
from app.services import notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _read(notification: Notification) -> NotificationRead:
    actor = None
    if notification.actor:
        actor = NotificationActorRead(
            id=notification.actor.id,
            full_name=notification.actor.full_name,
        )
    return NotificationRead(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        body=notification.body,
        link=notification.link,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at,
        actor=actor,
        metadata=notification.metadata_json or {},
    )


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    auth: AuthDep,
    db: DbDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[NotificationRead]:
    user = current_user(auth, db)
    rows = notification_service.list_notifications(db, user.id, limit)
    return [_read(row) for row in rows]


@router.get("/unread-count", response_model=UnreadCountRead)
def get_unread_count(auth: AuthDep, db: DbDep) -> UnreadCountRead:
    user = current_user(auth, db)
    return UnreadCountRead(count=notification_service.unread_count(db, user.id))


@router.patch("/read-all", response_model=MarkAllReadResult)
def mark_all_read(auth: AuthDep, db: DbDep) -> MarkAllReadResult:
    user = current_user(auth, db)
    updated = notification_service.mark_all_read(db, user.id)
    return MarkAllReadResult(updated=updated)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> NotificationRead:
    user = current_user(auth, db)
    notification = notification_service.mark_notification_read(
        db, notification_id, user.id
    )
    return _read(notification)
