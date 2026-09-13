"""Defense-in-depth sanitization for persisted MCP analytics snapshots."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from itertools import islice
from typing import Any

MAX_DEPTH = 12
MAX_CHILDREN = 100
MAX_STRING_LENGTH = 4_096
REDACTED = "[REDACTED]"
CREDENTIAL_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "password",
    "secret",
}
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")
_NAMED_CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(authorization|access_token|refresh_token|client_secret|api_key|password|secret)"
    r"\s*[:=]\s*[^\s,;]+"
)


def sanitize_snapshot(value: Any, *, max_bytes: int) -> dict[str, Any]:
    def walk(item: Any, depth: int) -> Any:
        if depth > MAX_DEPTH:
            return {"_truncated": "maximum_depth"}
        if item is None or isinstance(item, (bool, int)):
            return item
        if isinstance(item, float):
            return item if math.isfinite(item) else f"<{item}>"
        if isinstance(item, str):
            if len(item) <= MAX_STRING_LENGTH:
                return item
            marker = "…[truncated]"
            return item[: MAX_STRING_LENGTH - len(marker)] + marker
        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            entries = list(islice(item.items(), MAX_CHILDREN + 1))
            kept = entries[: MAX_CHILDREN - 1] if len(entries) > MAX_CHILDREN else entries
            for raw_key, child in kept:
                key = str(raw_key)[:MAX_STRING_LENGTH]
                result[key] = (
                    REDACTED
                    if key.casefold() in CREDENTIAL_KEYS
                    else walk(child, depth + 1)
                )
            if len(entries) > MAX_CHILDREN:
                result["_truncated_children"] = "at_least_one"
            return result
        if isinstance(item, (list, tuple)):
            children = list(islice(iter(item), MAX_CHILDREN + 1))
            kept = children[: MAX_CHILDREN - 1] if len(children) > MAX_CHILDREN else children
            result = [walk(child, depth + 1) for child in kept]
            if len(children) > MAX_CHILDREN:
                result.append({"_truncated_children": "at_least_one"})
            return result
        return f"<{type(item).__name__}>"

    sanitized = walk(value, 0)
    if not isinstance(sanitized, dict):
        sanitized = {"value": sanitized}
    encoded = json.dumps(
        sanitized,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) <= max_bytes:
        return sanitized
    return {
        "_mcp_log": {
            "truncated": True,
            "original_size_bytes": len(encoded),
            "limit_bytes": max_bytes,
        }
    }


def sanitize_error(value: Any, *, max_length: int = 2_000) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    without_bearer = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    sanitized = _NAMED_CREDENTIAL_PATTERN.sub(
        lambda match: f"{match.group(1)}=[REDACTED]",
        without_bearer,
    )
    return sanitized.strip()[:max_length]
