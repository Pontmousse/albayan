from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.core.clerk import AuthDep, DbDep
from app.core.config import settings
from app.core.deps import current_user
from app.schemas.agent_token import (
    AgentTokenCreate,
    AgentTokenCreated,
    AgentTokenRead,
    AgentTokenUpdate,
)
from app.services import agent_token_service

router = APIRouter(
    prefix="/api/v1/users/me/agent-tokens",
    tags=["agent-tokens"],
)


def _require_dev_mode() -> None:
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")


@router.get("", response_model=list[AgentTokenRead])
def list_my_agent_tokens(auth: AuthDep, db: DbDep) -> list[AgentTokenRead]:
    _require_dev_mode()
    user = current_user(auth, db)
    rows = agent_token_service.list_agent_tokens(db, user.id)
    return [AgentTokenRead.model_validate(row) for row in rows]


@router.post("", response_model=AgentTokenCreated, status_code=201)
def create_my_agent_token(
    payload: AgentTokenCreate,
    auth: AuthDep,
    db: DbDep,
) -> AgentTokenCreated:
    _require_dev_mode()
    user = current_user(auth, db)
    row, plaintext = agent_token_service.create_agent_token(
        db,
        user.id,
        payload.label,
        payload.scopes or [],
    )
    data = AgentTokenRead.model_validate(row).model_dump()
    return AgentTokenCreated(**data, token=plaintext)


@router.patch("/{token_id}", response_model=AgentTokenRead)
def update_my_agent_token(
    token_id: UUID,
    payload: AgentTokenUpdate,
    auth: AuthDep,
    db: DbDep,
) -> AgentTokenRead:
    _require_dev_mode()
    user = current_user(auth, db)
    row = agent_token_service.update_agent_token_label(
        db,
        user.id,
        token_id,
        payload.label,
    )
    return AgentTokenRead.model_validate(row)


@router.delete("/{token_id}", status_code=204)
def delete_my_agent_token(
    token_id: UUID,
    auth: AuthDep,
    db: DbDep,
) -> None:
    _require_dev_mode()
    user = current_user(auth, db)
    agent_token_service.delete_agent_token(db, user.id, token_id)
