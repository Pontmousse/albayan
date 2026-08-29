from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import IssueCategory, IssueStatus


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=20_000)
    category: IssueCategory

    @field_validator("title", "description", mode="before")
    @classmethod
    def _strip_surrounding_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class IssueReporterRead(BaseModel):
    id: UUID
    full_name: str | None


class IssueImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    s3_key: str
    position: int


class IssueRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    status: IssueStatus
    category: IssueCategory
    upvote_count: int
    current_user_upvoted: bool
    reporter: IssueReporterRead
    images: list[IssueImageRead]
    created_at: datetime
    updated_at: datetime
