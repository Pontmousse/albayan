from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    AccountDeletionRequestStatus,
    InvitationRole,
    InvitationStatus,
    IssueCategory,
    IssueStatus,
    ReviewerAssignmentStatus,
    UserGender,
    ArticleStatus,
)
from app.schemas.article import VersionRead
from app.schemas.editor import EditorReviewReport, ReviewerIdentityDisclosure
from app.schemas.issue import IssueImageRead


class AdminUserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None
    gender: UserGender | None


class AdminAuthorRead(BaseModel):
    user: AdminUserBrief
    author_order: int
    is_corresponding: bool


class AdminReviewerRead(BaseModel):
    id: UUID
    user: AdminUserBrief
    article_version_id: UUID
    version_number: int
    status: ReviewerAssignmentStatus
    invited_at: datetime
    review_due_at: datetime | None = None
    accepted_at: datetime | None
    declined_at: datetime | None


class AdminEditorRead(BaseModel):
    user: AdminUserBrief
    assigned_at: datetime
    assigned_by: UUID | None


class AdminArticleSummary(BaseModel):
    id: UUID
    title: str
    status: ArticleStatus
    latest_version_number: int | None
    updated_at: datetime
    submitted_at: datetime | None
    authors: list[AdminAuthorRead]
    reviewers: list[AdminReviewerRead]
    editors: list[AdminEditorRead]


class AdminArticleDetail(BaseModel):
    id: UUID
    title: str
    abstract: str | None
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime
    latest_version: VersionRead | None
    versions: list[VersionRead]
    authors: list[AdminAuthorRead]
    reviewers: list[AdminReviewerRead]
    editors: list[AdminEditorRead]
    reviews: list[EditorReviewReport]
    revision_request_note: str | None = None


class AssignByUserOrEmail(BaseModel):
    user_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    review_due_at: datetime | None = None

    @model_validator(mode="after")
    def require_one(self) -> "AssignByUserOrEmail":
        if not self.user_id and not self.email:
            raise ValueError("يلزم تحديد user_id أو email.")
        return self


class OverrideDecisionPayload(BaseModel):
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
        return self


class AdminUserListItem(BaseModel):
    id: UUID
    clerk_id: str
    email: str
    full_name: str | None
    gender: UserGender | None
    roles: list[str]
    created_at: datetime


class AdminStatusPayload(BaseModel):
    is_admin: bool


class AccountDeletionRequestStatusPayload(BaseModel):
    status: AccountDeletionRequestStatus
    resolution_note: str | None = Field(default=None, max_length=2000)


class AccountDeletionRequestAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email_snapshot: str
    reason: str | None
    status: str
    requested_at: datetime
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    resolution_note: str | None


class AppInvitationCreatePayload(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=200)
    gender: UserGender


class AppInvitationRead(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    gender: UserGender | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None


class AppInvitationCreateResponse(BaseModel):
    invitation: AppInvitationRead


class InviteCreatePayload(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: InvitationRole
    review_due_at: datetime | None = None

    @model_validator(mode="after")
    def require_reviewer_due_at(self) -> "InviteCreatePayload":
        if self.role == InvitationRole.REVIEWER and self.review_due_at is None:
            raise ValueError("يلزم تحديد موعد تسليم المراجعة.")
        return self


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_id: UUID
    article_version_id: UUID | None = None
    role: InvitationRole
    email: str
    status: InvitationStatus
    invited_by: UUID
    expires_at: datetime
    review_due_at: datetime | None = None
    created_at: datetime


class InvitationCreateResponse(BaseModel):
    invitation: InvitationRead
    warning: str | None = None


class AdminIssueReporterRead(BaseModel):
    id: UUID
    email: str
    full_name: str | None


class AdminIssueRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    status: IssueStatus
    category: IssueCategory
    upvote_count: int
    reporter: AdminIssueReporterRead
    images: list[IssueImageRead]
    created_at: datetime
    updated_at: datetime


class AdminIssueStatusPayload(BaseModel):
    status: IssueStatus
