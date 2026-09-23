from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class MathAuthoringCapabilitiesRead(BaseModel):
    """Machine-readable canonical LaTeX contract exposed to AI authoring clients."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal[1]
    canonical_input: Literal[True]
    representation: Literal["canonical_english_latex"]
    instruction: str
    preferred_submission: dict[str, Any]
    source_snapshot: dict[str, Any]
    round_trip_safe: dict[str, Any]
    accepted_but_not_round_trip_safe: dict[str, Any]
    unsupported_or_forbidden: dict[str, Any]
    normalization_aliases: list[dict[str, str]]
    constraints: list[str]
    examples: list[dict[str, Any]]
