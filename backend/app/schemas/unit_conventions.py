"""Article-specific unit conventions; Burhan remains the global registry owner."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Keep the wire contract deliberately compact; keys are case-sensitive canonical
# \mathsf{token} arguments, not LaTeX commands or display strings.
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_MAX_ENTRIES = 256
_MAX_TEXT = 128


class CustomUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1, max_length=_MAX_TEXT)
    display: str = Field(min_length=1, max_length=_MAX_TEXT)

    @field_validator("name", "display")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("unit name and display must not be blank")
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
            if not isinstance(display, str) or not display.strip() or len(display) > _MAX_TEXT:
                raise ValueError("unit override display must be a non-empty string")
        for token in self.custom_units:
            if not _TOKEN.fullmatch(token):
                raise ValueError("invalid canonical unit token")
        return self
