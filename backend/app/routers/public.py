from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.deps import DbDep
from app.schemas.public import PublicJournalResponse
from app.services import app_invitation_service, public_journal_service

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/journal", response_model=PublicJournalResponse)
def get_public_journal(db: DbDep) -> PublicJournalResponse:
    """حالة المجلة العامة — عدد المنشورات وقائمة المقالات المنشورة."""
    published_count, articles = public_journal_service.public_journal_summary(db)
    return PublicJournalResponse(
        published_count=published_count,
        articles=articles,
    )


def _handoff_page_url(token: str, status: str) -> str:
    site = settings.frontend_base_url.rstrip("/")
    return (
        f"{site}/tasjil/invitation/{quote(token, safe='')}"
        f"?status={quote(status, safe='')}"
    )


@router.post("/app-invitations/{token}/continue", response_class=RedirectResponse)
def continue_app_invitation_handoff(token: str) -> RedirectResponse:
    """Resolve the sensitive Clerk URL only after a deliberate form POST."""
    try:
        destination = app_invitation_service.continue_app_invitation_handoff(token)
    except HTTPException as exc:
        if exc.status_code == 410:
            status = "expired"
        elif exc.status_code in {404, 409}:
            status = "invalid"
        else:
            status = "unavailable"
        return RedirectResponse(_handoff_page_url(token, status), status_code=303)
    return RedirectResponse(destination, status_code=303)
