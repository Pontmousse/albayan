from fastapi import APIRouter, HTTPException, Request

from app.core.agent_auth import require_scope, resolve_agent_principal
from app.core.clerk import AuthDep, DbDep, get_auth_context
from app.core.config import settings
from app.core.deps import current_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import sync_clerk_name

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _read_user_me(request: Request, db: DbDep) -> UserRead:
    auth_header = request.headers.get("Authorization", "")
    if settings.dev_mode and auth_header.startswith("Bearer "):
        principal = resolve_agent_principal(request, db)
        require_scope(principal, "profile:read")
        user = db.get(User, principal.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="مفتاح الوكيل غير صالح.")
        return UserRead.model_validate(user)

    auth = get_auth_context(request)
    return UserRead.model_validate(current_user(auth, db))


@router.get("/me", response_model=UserRead)
def read_current_user(request: Request, db: DbDep) -> UserRead:
    return _read_user_me(request, db)


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    auth: AuthDep,
    db: DbDep,
) -> UserRead:
    user = current_user(auth, db)

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
