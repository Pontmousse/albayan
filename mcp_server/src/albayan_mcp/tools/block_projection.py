"""Compact MCP-only projection for canonical Document2 block reads."""

from __future__ import annotations

from typing import Any

_STRUCTURED_MATH_KEYS = {"math_objects", "caption_math_objects"}


def _strip_structured_math(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_structured_math(child)
            for key, child in value.items()
            if key not in _STRUCTURED_MATH_KEYS
        }
    if isinstance(value, list):
        return [_strip_structured_math(child) for child in value]
    return value


def project_draft_blocks_response(data: dict[str, Any]) -> dict[str, Any]:
    """Remove recursive equation AST sidecars while preserving all targeting metadata."""
    projected = dict(data)
    blocks = projected.get("blocks")
    if isinstance(blocks, list):
        projected["blocks"] = _strip_structured_math(blocks)
    return projected
