from fastapi import APIRouter

from app.core.deps import DbDep
from app.schemas.public import PublicJournalResponse
from app.services import public_journal_service

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/journal", response_model=PublicJournalResponse)
def get_public_journal(db: DbDep) -> PublicJournalResponse:
    """حالة المجلة العامة — عدد المنشورات وقائمة المقالات المنشورة."""
    published_count, articles = public_journal_service.public_journal_summary(db)
    return PublicJournalResponse(
        published_count=published_count,
        articles=articles,
    )
