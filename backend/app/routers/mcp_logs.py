from fastapi import APIRouter, HTTPException, Response

from app.core.actor import ActorDep
from app.core.clerk import DbDep
from app.core.config import settings
from app.schemas.mcp_analytics import McpCallLogCreate
from app.services import mcp_analytics_service

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp-internal"])


@router.post("/call-logs", status_code=204)
def create_mcp_call_log(
    payload: McpCallLogCreate,
    actor: ActorDep,
    db: DbDep,
) -> Response:
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="غير موجود.")
    if actor.auth_method != "agent":
        raise HTTPException(status_code=403, detail="هذا المسار مخصص للوكلاء.")
    mcp_analytics_service.create_call_log(
        db,
        user_id=actor.user_id,
        payload=payload,
    )
    return Response(status_code=204)
