from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PublicArticleAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None
    author_order: int


class PublicArticleSummary(BaseModel):
    """مقال منشور للعرض العام — بدون بيانات داخلية."""

    id: UUID
    title: str
    abstract: str | None
    published_at: datetime
    authors: list[PublicArticleAuthor]


class PublicJournalResponse(BaseModel):
    """حالة المجلة العامة — مصدر الحقيقة لانتقال واجهة الرئيسية."""

    published_count: int
    articles: list[PublicArticleSummary]
