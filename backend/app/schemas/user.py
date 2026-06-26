from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clerk_id: str
    email: str
    full_name: str | None
    affiliation: str | None
    bio: str | None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    affiliation: str | None = Field(default=None, max_length=300)
    bio: str | None = Field(default=None, max_length=500)
