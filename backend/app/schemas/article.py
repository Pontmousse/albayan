from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CompileStatus, SourceType, VersionStatus


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)


class VersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    status: VersionStatus
    source_type: SourceType
    compile_status: CompileStatus
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
