"""Typed used-unit inventory and revision-producing convention update."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.article import DraftRevisionRead
from app.schemas.unit_conventions import UnitConventions


class UsedUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    usage_count: int = Field(ge=1)
    status: Literal["registry", "custom", "unknown"]
    display: str
    source: Literal["registry_default", "article_override", "article_custom", "unknown"]
    name: str | None = None
    name_ar: str | None = None
    default_display: str | None = None
    alternatives: list[str] = Field(default_factory=list)


class UsedUnitInventory(BaseModel):
    revision_number: int = Field(ge=1)
    unit_conventions: UnitConventions
    used_units: list[UsedUnit]
    registered_tokens: list[str] = Field(default_factory=list)


class ApplyUnitConventionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    base_revision: int = Field(ge=1)
    unit_conventions: UnitConventions


class ApplyUnitConventionsResult(DraftRevisionRead):
    affected_block_ids: list[str] = Field(default_factory=list)
    used_units: list[UsedUnit] = Field(default_factory=list)
