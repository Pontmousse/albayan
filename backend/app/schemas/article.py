from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    ArticleStatus,
    CompileStatus,
    DraftActorType,
    DraftRevisionReason,
    SourceType,
    ReviewRecommendation,
)
from app.schemas.document2 import DocumentCommand


class ArticleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)

    @field_validator("title", "abstract", mode="before")
    @classmethod
    def _strip_surrounding_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ArticleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(ge=1, strict=True)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)

    @field_validator("title", "abstract", mode="before")
    @classmethod
    def _strip_surrounding_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _require_a_metadata_change(self):
        if not self.model_fields_set.intersection({"title", "abstract"}):
            raise ValueError("يجب إرسال title أو abstract على الأقل.")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title لا يقبل null.")
        return self


class VersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    source_type: SourceType
    source_draft_revision_id: UUID | None = None
    document_hash: str
    title_snapshot: str
    abstract_snapshot: str | None
    submitted_at: datetime | None
    created_at: datetime


class ArticleSummary(BaseModel):
    """صف واحد في قائمة «مقالاتي» — المقال + حالة إصداره الحالي."""

    id: UUID
    title: str
    status: ArticleStatus
    latest_version_number: int | None
    updated_at: datetime
    submitted_at: datetime | None


class AuthorRevisionFeedback(BaseModel):
    review_id: UUID
    reviewer_label: str
    comments_to_author: str
    recommendation: ReviewRecommendation | None = None


class ArticleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    abstract: str | None
    status: ArticleStatus
    current_draft_revision_id: UUID | None
    draft_revision_number: int
    created_at: datetime
    updated_at: datetime
    revision_request_note: str | None = None
    revision_requested_for_version_id: UUID | None = None
    revision_requested_at: datetime | None = None
    revision_feedback: list[AuthorRevisionFeedback] = Field(default_factory=list)
    latest_version: VersionRead | None
    versions: list[VersionRead]


class ArticleAssetRead(BaseModel):
    """أصل صورة مخزّن في S3 تحت assets/ — بدون جدول قاعدة بيانات."""

    asset_id: str
    content_type: str | None = None
    size: int = 0
    updated_at: datetime | None = None


class ArticleAssetsList(BaseModel):
    assets: list[ArticleAssetRead]


class ArticleAssetUploadRead(BaseModel):
    asset_id: str
    content_type: str
    size: int = Field(ge=1)


class DraftCompileError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class DraftCompileStatusRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CompileStatus
    compile_id: UUID | None = None
    revision_id: UUID
    revision_number: int
    pdf_ready: bool
    error: DraftCompileError | None = None


class DocumentCommandPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: UUID
    base_revision: int = Field(ge=1, strict=True)
    command: DocumentCommand


class DraftUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(ge=1, strict=True)
    document: Any


class DraftRevisionRead(BaseModel):
    revision_id: UUID
    revision_number: int
    document_hash: str
    actor_type: DraftActorType
    reason: DraftRevisionReason
    created_at: datetime
    restored_from_id: UUID | None = None
    restored_from_revision_number: int | None = None
    document: Any


class DraftRevisionHistoryItem(BaseModel):
    revision_id: UUID
    revision_number: int
    document_hash: str
    actor_type: DraftActorType
    reason: DraftRevisionReason
    created_at: datetime
    created_by: UUID | None = None
    created_by_name: str | None = None
    restored_from_id: UUID | None = None
    restored_from_revision_number: int | None = None
    is_current: bool


class DraftRevisionHistoryDetail(DraftRevisionHistoryItem):
    document: Any


class DraftRestorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(ge=1, strict=True)


class DocumentOutlineEntry(BaseModel):
    id: str
    kind: Literal[
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "list",
        "table",
        "figure",
        "bibliography",
        "raw",
    ]
    command: str | None = None
    excerpt: str


class DocumentOutlineRead(BaseModel):
    revision_id: UUID
    revision_number: int
    outline: list[DocumentOutlineEntry]


class DocumentBlocksRead(BaseModel):
    revision_id: UUID
    revision_number: int
    blocks: list[Any]


class DocumentReferenceRead(BaseModel):
    key: str
    authors: str
    title: str
    year: str
    venue: str
    url: str
    field_separator: Literal[",", "،"]


class DraftReferencesRead(BaseModel):
    revision_id: UUID
    revision_number: int
    references: list[DocumentReferenceRead]


class DocumentCitationIndexEntry(BaseModel):
    kind: Literal["cite"]
    block_id: str
    field_id: str
    token_id: str
    keys: list[str]
    unresolved_keys: list[str]


class DocumentCrossReferenceIndexEntry(BaseModel):
    kind: Literal["ref"]
    ref_command: Literal["ref", "eqref"]
    block_id: str
    field_id: str
    token_id: str
    keys: list[str]
    unresolved_keys: list[str]


class DocumentIndexedLabel(BaseModel):
    key: str
    kind: Literal["fig", "tab", "eq"]
    caption: str
    number: int = Field(ge=1)
    block_id: str | None = None
    field_id: str | None = None
    token_id: str | None = None


class DocumentUnresolvedReferences(BaseModel):
    citation_keys: list[str]
    cross_reference_keys: list[str]


class DocumentReferenceIndex(BaseModel):
    citations: list[DocumentCitationIndexEntry]
    cross_references: list[DocumentCrossReferenceIndexEntry]
    labels: list[DocumentIndexedLabel]
    unresolved: DocumentUnresolvedReferences


class DraftReferenceIndexRead(BaseModel):
    revision_id: UUID
    revision_number: int
    reference_index: DocumentReferenceIndex


class DocumentCommandResult(BaseModel):
    ok: bool = True
    revision_id: UUID
    revision_number: int
    document_hash: str
    actor_type: DraftActorType
    reason: DraftRevisionReason
    document: Any
    affected_block_ids: list[str] = Field(default_factory=list)
