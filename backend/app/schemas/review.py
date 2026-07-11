from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ReviewRecommendation,
    ReviewerAssignmentStatus,
    ReviewStatus,
    VersionStatus,
)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    comments_to_author: str | None
    comments_to_editor: str | None
    recommendation: ReviewRecommendation | None
    status: ReviewStatus
    submitted_at: datetime | None
    article_version_id: UUID


class ReviewWrite(BaseModel):
    comments_to_author: str | None = Field(default=None, max_length=20000)
    comments_to_editor: str | None = Field(default=None, max_length=20000)
    recommendation: ReviewRecommendation | None = None


class AssignmentSummary(BaseModel):
    id: UUID
    article_id: UUID
    article_title: str
    assignment_status: ReviewerAssignmentStatus
    version_status: VersionStatus
    version_number: int
    review: ReviewRead | None
    invited_at: datetime


class AssignmentDetail(BaseModel):
    id: UUID
    article_id: UUID
    article_title: str
    article_abstract: str | None
    assignment_status: ReviewerAssignmentStatus
    version_status: VersionStatus
    version_number: int
    version_id: UUID
    review: ReviewRead | None
    invited_at: datetime
    accepted_at: datetime | None
