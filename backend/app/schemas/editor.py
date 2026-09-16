from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ArticleStatus, ReviewRecommendation
from app.schemas.article import VersionRead


class EditorArticleSummary(BaseModel):
    id: UUID
    title: str
    status: ArticleStatus
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
    reveal_reviewer_identity_to_author: bool = False


class EditorArticleDetail(BaseModel):
    id: UUID
    title: str
    abstract: str | None
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime
    latest_version: VersionRead
    versions: list[VersionRead]
    reviews: list[EditorReviewReport]


class ReviewerIdentityDisclosure(BaseModel):
    review_id: UUID
    reveal_identity: bool = False


class EditorDecisionPayload(BaseModel):
    status: ArticleStatus
    reason: str | None = Field(default=None, max_length=2000)
    reviewer_identity_disclosures: list[ReviewerIdentityDisclosure] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def require_revision_note(self):
        if self.status == ArticleStatus.REVISION_REQUESTED and not (
            self.reason and self.reason.strip()
        ):
            raise ValueError("يلزم كتابة توجيهات التعديل.")
        if self.status != ArticleStatus.REVISION_REQUESTED and self.reviewer_identity_disclosures:
            raise ValueError("إعدادات كشف الهوية متاحة مع طلب التعديل فقط.")
        return self
