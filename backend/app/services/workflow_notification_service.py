import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.enums import NotificationType
from app.models.user import User
from app.services import notification_service


def admin_ids(db: Session) -> set[uuid.UUID]:
    return set(db.scalars(select(User.id).where(User.is_admin.is_(True))).all())


def author_ids(article: Article) -> set[uuid.UUID]:
    return {link.user_id for link in article.author_links}


def notify_many(
    db: Session,
    *,
    user_ids: Iterable[uuid.UUID],
    type: NotificationType,
    title: str,
    body: str | None,
    link: str | None,
    event_scope: str,
    actor_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    notification_service.create_notifications(
        db,
        user_ids=set(user_ids),
        type=type,
        title=title,
        body=body,
        link=link,
        actor_id=actor_id,
        metadata=metadata,
        event_scope=event_scope,
    )
