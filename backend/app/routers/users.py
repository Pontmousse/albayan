from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import OperationalError

from app.core.clerk import AuthDep, DbDep
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import get_or_create_user, sync_clerk_name

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(auth: AuthDep, db: DbDep) -> UserRead:
    try:
        user = get_or_create_user(db, auth)
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="الخدمة غير متاحة مؤقتاً.",
        ) from exc
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    auth: AuthDep,
    db: DbDep,
) -> UserRead:
    try:
        user = get_or_create_user(db, auth)
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="الخدمة غير متاحة مؤقتاً.",
        ) from exc

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    if "full_name" in updates:
        try:
            sync_clerk_name(auth.clerk_id, user.full_name)
        except Exception:
            pass

    return UserRead.model_validate(user)
