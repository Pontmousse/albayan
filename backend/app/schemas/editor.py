from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewRecommendation, VersionStatus
from app.schemas.article import VersionRead


class EditorArticleSummary(BaseModel):
    id: UUID
    title: str
    status: VersionStatus
    version_number: int
    updated_at: datetime
    submitted_at: datetime | None
    submitted_reviews_count: int = 0


class EditorReviewReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reviewer_name: str | None
    reviewer_email: str
    comments_to_author: str | None
    comments_to_editor: str | None
    recommendation: ReviewRecommendation | None
    submitted_at: datetime | None


class EditorArticleDetail(BaseModel):
    id: UUID
    title: str
    abstract: str | None
    created_at: datetime
    updated_at: datetime
    current_version: VersionRead
    versions: list[VersionRead]
    reviews: list[EditorReviewReport]


class EditorDecisionPayload(BaseModel):
    status: VersionStatus
    reason: str | None = Field(default=None, max_length=2000)
