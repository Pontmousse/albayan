import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import clerk_client
from app.models.article import ArticleAuthor, ArticleEditor, ArticleReviewer
from app.models.enums import NotificationType
from app.models.user import User
from app.services import workflow_notification_service

_NOT_FOUND = HTTPException(status_code=404, detail="المستخدم غير موجود.")


def list_users_with_roles(db: Session) -> list[dict]:
    users = list(db.scalars(select(User).order_by(User.created_at.desc())).all())
    author_ids = {
        row for row in db.scalars(select(ArticleAuthor.user_id)).all()
    }
    reviewer_ids = {
        row for row in db.scalars(select(ArticleReviewer.user_id)).all()
    }
    editor_ids = {
        row for row in db.scalars(select(ArticleEditor.user_id)).all()
    }

    result = []
    for user in users:
        roles: list[str] = []
        if user.id in author_ids:
            roles.append("author")
        if user.id in reviewer_ids:
            roles.append("reviewer")
        if user.id in editor_ids:
            roles.append("editor")
        if user.is_admin:
            roles.append("admin")
        result.append(
            {
                "id": user.id,
                "clerk_id": user.clerk_id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": roles,
                "created_at": user.created_at,
            }
        )
    return result


def set_admin_status(
    db: Session,
    user_id: uuid.UUID,
    is_admin: bool,
    *,
    actor_id: uuid.UUID | None = None,
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise _NOT_FOUND
    changed = user.is_admin != is_admin

    public_metadata: dict = {"role": "admin"} if is_admin else {"role": None}
    try:
        # Deep-merge: setting role to null removes the key in Clerk metadata APIs.
        clerk_client.users.update_metadata(
            user_id=user.clerk_id,
            public_metadata=public_metadata,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="تعذّر تحديث صلاحيات المدير في Clerk.",
        ) from exc

    if not changed:
        return user

    user.is_admin = is_admin
    workflow_notification_service.notify_many(
        db,
        user_ids={user.id},
        type=NotificationType.ADMIN_ROLE_CHANGED,
        title="تغيّرت صلاحيات حسابك",
        body=(
            "مُنحت صلاحية إدارة مجلة البيان."
            if is_admin
            else "أُزيلت صلاحية إدارة مجلة البيان من حسابك."
        ),
        link="/admin" if is_admin else "/maktabi",
        actor_id=actor_id,
        event_scope=(
            f"user:{user.id}:admin-role:{'granted' if is_admin else 'removed'}:"
            f"{uuid.uuid4()}"
        ),
        metadata={"is_admin": is_admin},
    )
    db.commit()
    db.refresh(user)
    return user


def reconcile_admin_roles(db: Session) -> int:
    users_by_clerk_id = {
        user.clerk_id: user for user in db.scalars(select(User)).all()
    }
    changed = 0
    offset = 0
    while offset < 100_000:
        rows = clerk_client.users.list(request={"limit": 100, "offset": offset})
        if not rows:
            break
        for clerk_user in rows:
            clerk_id = str(getattr(clerk_user, "id", ""))
            local_user = users_by_clerk_id.get(clerk_id)
            if local_user is None:
                continue
            metadata = getattr(clerk_user, "public_metadata", None)
            role = metadata.get("role") if isinstance(metadata, dict) else None
            expected = role == "admin"
            if local_user.is_admin != expected:
                local_user.is_admin = expected
                changed += 1
        if len(rows) < 100:
            break
        offset += len(rows)
    if changed:
        db.commit()
    return changed
