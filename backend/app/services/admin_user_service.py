import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import clerk_client
from app.models.article import ArticleAuthor, ArticleEditor, ArticleReviewer
from app.models.user import User

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


def set_admin_status(db: Session, user_id: uuid.UUID, is_admin: bool) -> User:
    user = db.get(User, user_id)
    if not user:
        raise _NOT_FOUND

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

    return user
