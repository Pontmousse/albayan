"""مشتركات الاعتماديات بين الراوترات."""

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.core.clerk import AuthContext, DbDep
from app.models.user import User
from app.services.user_service import get_or_create_user

DB_UNAVAILABLE = HTTPException(status_code=503, detail="الخدمة غير متاحة مؤقتاً.")


def current_user(auth: AuthContext, db: DbDep) -> User:
    try:
        return get_or_create_user(db, auth)
    except OperationalError as exc:
        raise DB_UNAVAILABLE from exc
