"""Article-specific unit conventions; Burhan owns canonical unit identities."""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Mirrored syntax-only wire contract; registry membership comes from Burhan.
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_ALLOWED_PUNCTUATION = frozenset(".·-٫")
_MAX_ENTRIES = 256
_MAX_DISPLAY = 64


def _validate_display(value: str) -> str:
    """Match Burhan's plain-text (never LaTeX) unit display grammar."""
    if not value or len(value) > _MAX_DISPLAY:
        raise ValueError("unit display must be 1–64 characters")
    if value != value.strip() or "  " in value:
        raise ValueError("unit display must have single, trimmed spaces")
    if not any(unicodedata.category(ch).startswith("L") for ch in value):
        raise ValueError("unit display must contain a letter")
    for ch in value:
        if ch == " " or ch in _ALLOWED_PUNCTUATION:
            continue
        if unicodedata.category(ch)[0] in "LMN":
            continue
        raise ValueError("unit displays must be plain Unicode text, not LaTeX")
    return value


class CustomUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    display: str
    name: str | None = Field(default=None, max_length=100)

    @field_validator("display")
    @classmethod
    def _check_display(cls, value: str) -> str:
        return _validate_display(value)

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("custom unit name must be trimmed and nonblank")
        return value


class UnitConventions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    overrides: dict[str, str] = Field(default_factory=dict)
    custom_units: dict[str, CustomUnit] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_tokens(self) -> "UnitConventions":
        if len(self.overrides) > _MAX_ENTRIES or len(self.custom_units) > _MAX_ENTRIES:
            raise ValueError("too many unit conventions")
        if self.overrides.keys() & self.custom_units.keys():
            raise ValueError("custom units and overrides must be disjoint")
        for token, display in self.overrides.items():
            if not _TOKEN.fullmatch(token):
                raise ValueError("invalid canonical unit token")
            _validate_display(display)
        for token in self.custom_units:
            if not _TOKEN.fullmatch(token):
                raise ValueError("invalid canonical unit token")
        return self
