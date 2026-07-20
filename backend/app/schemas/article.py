from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
