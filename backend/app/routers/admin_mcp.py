import uuid

from fastapi import APIRouter, HTTPException, Query

from app.core.clerk import AdminDep, DbDep
from app.core.config import settings
from app.core.deps import current_user
from app.schemas.mcp_analytics import (
    McpAnalyticsPeriod,
    McpAnalyticsRead,
    McpCallDetailRead,
    McpCallListRead,
    McpCallStatus,
)
from app.services import mcp_analytics_service

router = APIRouter(prefix="/api/v1/admin/mcp", tags=["admin-mcp"])


def _require_admin_feature(auth: AdminDep, db: DbDep) -> None:
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="غير موجود.")
    user = current_user(auth, db)
    if not user.is_admin:
        user.is_admin = True
        db.commit()
        db.refresh(user)


@router.get("/analytics", response_model=McpAnalyticsRead)
def get_mcp_analytics(
    auth: AdminDep,
    db: DbDep,
    period: McpAnalyticsPeriod = Query(default="7d"),
) -> McpAnalyticsRead:
    _require_admin_feature(auth, db)
    return mcp_analytics_service.analytics(db, period)


@router.get("/calls", response_model=McpCallListRead)
def list_mcp_calls(
    auth: AdminDep,
    db: DbDep,
    period: McpAnalyticsPeriod = Query(default="7d"),
    tool: str | None = Query(default=None, min_length=1, max_length=100),
    command: str | None = Query(default=None, min_length=1, max_length=100),
    status: McpCallStatus | None = Query(default=None),
    cursor: str | None = Query(default=None, max_length=500),
    limit: int = Query(default=50, ge=1, le=100),
) -> McpCallListRead:
    _require_admin_feature(auth, db)
    return mcp_analytics_service.list_calls(
        db,
        period=period,
        tool_name=tool,
        command_name=command,
        status=status,
        cursor=cursor,
        limit=limit,
    )


@router.get("/calls/{call_id}", response_model=McpCallDetailRead)
def get_mcp_call(
    call_id: uuid.UUID,
    auth: AdminDep,
    db: DbDep,
) -> McpCallDetailRead:
    _require_admin_feature(auth, db)
    return mcp_analytics_service.get_call(db, call_id)
