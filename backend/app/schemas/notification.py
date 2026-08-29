from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationActorRead(BaseModel):
    id: UUID
    full_name: str | None


class NotificationRead(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: str | None
    link: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    actor: NotificationActorRead | None = None
    metadata: dict[str, Any]


class UnreadCountRead(BaseModel):
    count: int


class MarkAllReadResult(BaseModel):
    ok: bool = True
    updated: int
