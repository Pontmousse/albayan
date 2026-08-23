import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.agent_token_service import (
    ALLOWED_AGENT_SCOPES,
    DEFAULT_AGENT_SCOPES,
    normalize_scopes,
)


class AgentTokenCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] | None = None

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("اسم المفتاح مطلوب.")
        return trimmed

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return list(DEFAULT_AGENT_SCOPES)
        return normalize_scopes(value)


class AgentTokenUpdate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("اسم المفتاح مطلوب.")
        return trimmed


class AgentTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    scopes: list[str]
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentTokenCreated(AgentTokenRead):
    token: str = Field(
        ...,
        description="يُعرض مرة واحدة عند الإنشاء فقط.",
    )


class AgentScopeOption(BaseModel):
    value: str
    label: str


def scope_options() -> list[AgentScopeOption]:
    labels = {
        "profile:read": "قراءة الملف الشخصي",
        "articles:read": "قراءة المقالات",
        "articles:session:write": "كتابة مسودة الجلسة",
        "reviews:read": "قراءة تعيينات المراجعة",
        "reviews:draft:write": "مسودة ملاحظات المراجعة",
        "editor:read": "قراءة مقالات التحرير",
    }
    return [
        AgentScopeOption(value=scope, label=labels.get(scope, scope))
        for scope in sorted(ALLOWED_AGENT_SCOPES)
    ]
