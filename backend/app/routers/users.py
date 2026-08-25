from fastapi import APIRouter

from app.core.actor import ActorDep, current_actor_user
from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import sync_clerk_name

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(actor: ActorDep, db: DbDep) -> UserRead:
    # Read-only profile access is agent-safe.
    return UserRead.model_validate(current_actor_user(actor, db))


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
