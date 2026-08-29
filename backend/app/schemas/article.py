from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CompileStatus, SourceType, VersionStatus


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)


class ArticleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)

    @field_validator("title", "abstract", mode="before")
    @classmethod
    def _strip_surrounding_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class VersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    status: VersionStatus
    source_type: SourceType
    compile_status: CompileStatus
    active_compile_id: UUID | None = None
    compiled_document_hash: str | None = None
    change_summary: str | None
    submitted_at: datetime | None
    created_at: datetime


class ArticleSummary(BaseModel):
    """صف واحد في قائمة «مقالاتي» — المقال + حالة إصداره الحالي."""

    id: UUID
    title: str
    status: VersionStatus
    version_number: int
    updated_at: datetime
    submitted_at: datetime | None


class ArticleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    abstract: str | None
    created_at: datetime
    updated_at: datetime
    current_version: VersionRead
    versions: list[VersionRead]


class ArticleAssetRead(BaseModel):
    """أصل صورة مخزّن في S3 تحت assets/ — بدون جدول قاعدة بيانات."""

    asset_id: str
    content_type: str | None = None
    size: int = 0
    updated_at: datetime | None = None


class ArticleAssetsList(BaseModel):
    assets: list[ArticleAssetRead]


class DocumentPayload(BaseModel):
    document: Any


class CompilePayload(BaseModel):
    latex: str = Field(min_length=1, max_length=300_000)
    asset_keys: list[str] = Field(default_factory=list, max_length=50)
    document_hash: str = Field(min_length=64, max_length=64)

    @field_validator("document_hash")
    @classmethod
    def _hash_hex(cls, value: str) -> str:
        lowered = value.strip().lower()
        if len(lowered) != 64 or any(c not in "0123456789abcdef" for c in lowered):
            raise ValueError("document_hash يجب أن يكون SHA-256 hex بطول 64.")
        return lowered


class DocumentAnchor(BaseModel):
    after_block_id: str | None = None
    end: bool | None = None

    @model_validator(mode="after")
    def _exactly_one_anchor(self) -> "DocumentAnchor":
        has_after = bool(self.after_block_id)
        has_end = self.end is True
        if has_after == has_end:
            raise ValueError("حدد after_block_id أو end فقط.")
        return self


DocumentTextKind = Literal["section", "subsection", "subsubsection", "paragraph"]


class InsertTextBlockCommand(BaseModel):
    op: Literal["insert_text_block"]
    kind: DocumentTextKind
    text: str
    anchor: DocumentAnchor


class ReplaceTextBlockCommand(BaseModel):
    op: Literal["replace_text_block"]
    block_id: str
    text: str


class RemoveBlockCommand(BaseModel):
    op: Literal["remove_block"]
    block_id: str


class InsertFigureCommand(BaseModel):
    op: Literal["insert_figure"]
    asset_id: str
    value: str | None = None
    caption: str | None = None
    label: str | None = None
    anchor: DocumentAnchor


DocumentCommand = Annotated[
    InsertTextBlockCommand
    | ReplaceTextBlockCommand
    | RemoveBlockCommand
    | InsertFigureCommand,
    Field(discriminator="op"),
]


class DocumentCommandPayload(BaseModel):
    command_id: UUID
    base_revision: int = Field(ge=0)
    command: DocumentCommand


class DocumentSessionUpdatePayload(BaseModel):
    base_revision: int = Field(ge=0)
    document: Any


class DocumentSessionRead(BaseModel):
    revision: int
    last_saved_revision: int
    document: Any


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
    revision: int
    last_saved_revision: int
    outline: list[DocumentOutlineEntry]


class DocumentBlocksRead(BaseModel):
    revision: int
    last_saved_revision: int
    blocks: list[Any]


class DocumentCommandResult(BaseModel):
    ok: bool = True
    revision: int
    last_saved_revision: int
    document: Any
    affected_block_ids: list[str] = Field(default_factory=list)


class DocumentSessionSaveResult(BaseModel):
    ok: bool = True
    revision: int
    last_saved_revision: int
