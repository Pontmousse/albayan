from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    InvitationRole,
    InvitationStatus,
    ReviewerAssignmentStatus,
    VersionStatus,
)
from app.schemas.article import VersionRead


class AdminUserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None


class AdminAuthorRead(BaseModel):
    user: AdminUserBrief
    author_order: int
    is_corresponding: bool


class AdminReviewerRead(BaseModel):
    user: AdminUserBrief
    status: ReviewerAssignmentStatus
    invited_at: datetime
    accepted_at: datetime | None
    declined_at: datetime | None


class AdminEditorRead(BaseModel):
    user: AdminUserBrief
    assigned_at: datetime
    assigned_by: UUID | None


class AdminArticleSummary(BaseModel):
    id: UUID
    title: str
    status: VersionStatus
    version_number: int
    updated_at: datetime
    submitted_at: datetime | None
    authors: list[AdminAuthorRead]
    reviewers: list[AdminReviewerRead]
    editors: list[AdminEditorRead]


class AdminArticleDetail(BaseModel):
    id: UUID
    title: str
    abstract: str | None
    created_at: datetime
    updated_at: datetime
    current_version: VersionRead
    versions: list[VersionRead]
    authors: list[AdminAuthorRead]
    reviewers: list[AdminReviewerRead]
    editors: list[AdminEditorRead]


class AssignByUserOrEmail(BaseModel):
    user_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)

    @model_validator(mode="after")
    def require_one(self) -> "AssignByUserOrEmail":
        if not self.user_id and not self.email:
            raise ValueError("يلزم تحديد user_id أو email.")
        return self


class OverrideDecisionPayload(BaseModel):
    status: VersionStatus
    reason: str | None = Field(default=None, max_length=2000)


class AdminUserListItem(BaseModel):
    id: UUID
    clerk_id: str
    email: str
    full_name: str | None
    roles: list[str]
    created_at: datetime


class AdminStatusPayload(BaseModel):
    is_admin: bool


class InviteCreatePayload(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: InvitationRole


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_id: UUID
    role: InvitationRole
    email: str
    status: InvitationStatus
    invited_by: UUID
    expires_at: datetime
    created_at: datetime


class InvitationCreateResponse(BaseModel):
    invitation: InvitationRead
    warning: str | None = None
