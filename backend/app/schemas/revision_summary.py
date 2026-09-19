from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RevisionChangeKind = Literal[
    "added",
    "removed",
    "edited",
    "moved",
    "metadata",
    "other",
]


class RevisionChangeSummaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: RevisionChangeKind
    text: str = Field(min_length=1, max_length=300)

    @field_validator("text")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("summary text cannot be empty")
        return stripped


class RevisionChangeSummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    items: list[RevisionChangeSummaryItem] = Field(default_factory=list, max_length=4)


class DraftRevisionChangeSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: RevisionChangeSummaryV1 | None
