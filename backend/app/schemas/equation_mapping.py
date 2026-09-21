from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

_MAX_MAPPINGS = 256
_MAX_SYMBOL_LENGTH = 128


class EquationMappingsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mappings: dict[str, str]


class EquationMappingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mappings: dict[str, str]

    @field_validator("mappings", mode="before")
    @classmethod
    def _validate_mappings(cls, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            raise ValueError("mappings must be a JSON object")
        if len(value) > _MAX_MAPPINGS:
            raise ValueError(f"mappings supports at most {_MAX_MAPPINGS} entries")

        normalized: dict[str, str] = {}
        for english, arabic in value.items():
            if not isinstance(english, str) or not isinstance(arabic, str):
                raise ValueError("mapping keys and values must be strings")
            english = english.strip()
            arabic = arabic.strip()
            if not english or not arabic:
                raise ValueError("mapping keys and values must be non-empty strings")
            if len(english) > _MAX_SYMBOL_LENGTH or len(arabic) > _MAX_SYMBOL_LENGTH:
                raise ValueError(
                    f"mapping keys and values must be at most {_MAX_SYMBOL_LENGTH} characters"
                )
            normalized[english] = arabic
        return normalized
