from __future__ import annotations

import re
from typing import Any

_SECRET_KEY_PARTS = (
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


def sanitize(value: Any) -> Any:
    """Best-effort redaction for developer-facing diagnostic output."""

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                result[key_text] = "[REDACTED]"
            else:
                result[key_text] = sanitize(item)
        return result
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return _BEARER_RE.sub("Bearer [REDACTED]", value)
    return value
