import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.enums import NotificationType
from app.models.notification import Notification

_NOT_FOUND = HTTPException(status_code=404, detail="الإشعار غير موجود.")


def create_notification(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    title: str,
    body: str | None = None,
    link: str | None = None,
    actor_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    event_key: str | None = None,
) -> Notification:
    if event_key:
        existing = db.scalar(
            select(Notification).where(Notification.event_key == event_key)
        )
        if existing:
            return existing

    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        link=link,
        actor_id=actor_id,
        metadata_json=metadata or {},
        event_key=event_key,
        is_read=False,
        read_at=None,
    )
    db.add(notification)
    db.flush()
    return notification


def create_notifications(
    db: Session,
    *,
    user_ids: list[uuid.UUID] | set[uuid.UUID] | tuple[uuid.UUID, ...],
    type: NotificationType,
    title: str,
    body: str | None = None,
    link: str | None = None,
    actor_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    event_scope: str,
) -> list[Notification]:
    return [
        create_notification(
            db,
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            link=link,
            actor_id=actor_id,
            metadata=metadata,
            event_key=f"{event_scope}:user:{user_id}",
        )
        for user_id in sorted(set(user_ids), key=str)
    ]


def list_notifications(
    db: Session, user_id: uuid.UUID, limit: int = 10
) -> list[Notification]:
    bounded_limit = max(1, min(limit, 50))
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .options(selectinload(Notification.actor))
            .order_by(Notification.created_at.desc())
            .limit(bounded_limit)
        ).all()
    )


def list_notifications_page(
    db: Session,
    user_id: uuid.UUID,
    *,
    limit: int = 20,
    before: datetime | None = None,
) -> tuple[list[Notification], datetime | None]:
    bounded_limit = max(1, min(limit, 50))
    statement = select(Notification).where(Notification.user_id == user_id)
    if before is not None:
        statement = statement.where(Notification.created_at < before)
    statement = (
        statement.options(selectinload(Notification.actor))
        .order_by(Notification.created_at.desc())
        .limit(bounded_limit + 1)
    )

    rows = list(db.scalars(statement).all())
    items = rows[:bounded_limit]
    next_cursor = items[-1].created_at if len(rows) > bounded_limit and items else None
    return items, next_cursor


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )


def mark_notification_read(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification:
    notification = db.scalar(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .options(selectinload(Notification.actor))
    )
    if not notification:
        raise _NOT_FOUND

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    db.commit()
    return int(result.rowcount or 0)
