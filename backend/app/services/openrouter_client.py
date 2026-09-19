"""Server-only OpenRouter client for revision change summaries."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.revision_summary_config import revision_summary_settings
from app.schemas.revision_summary import RevisionChangeSummaryV1

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT_SECONDS = 20.0

_SYSTEM_PROMPT = """You summarize changes between two immutable revisions of an academic document.
Return concise Arabic text only through the required JSON schema.
Describe only facts supported by the supplied diff. Do not infer motives, quality, intent, or changes not present in the diff.
Use at most four items. Classify each item as added, removed, edited, moved, metadata, or other.
Prefer a single clear sentence per item."""

_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "albayan_revision_change_summary_v1",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "version": {"type": "integer", "const": 1},
                "items": {
                    "type": "array",
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": [
                                    "added",
                                    "removed",
                                    "edited",
                                    "moved",
                                    "metadata",
                                    "other",
                                ],
                            },
                            "text": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 300,
                            },
                        },
                        "required": ["kind", "text"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["version", "items"],
            "additionalProperties": False,
        },
    },
}


def _parse_summary(content: Any) -> dict[str, Any] | None:
    try:
        if isinstance(content, str):
            summary = RevisionChangeSummaryV1.model_validate_json(content)
        elif isinstance(content, dict):
            summary = RevisionChangeSummaryV1.model_validate(content)
        else:
            return None
    except (ValidationError, ValueError, TypeError):
        return None
    return summary.model_dump(mode="json")


def summarize_revision_diff(diff: dict[str, Any]) -> dict[str, Any] | None:
    api_key = revision_summary_settings.openrouter_api_key.get_secret_value().strip()
    model = revision_summary_settings.openrouter_model.strip() or "openrouter/free"
    if not api_key:
        logger.info("Revision summary unavailable: OPENROUTER_API_KEY is not configured")
        return None

    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"diff": diff}, ensure_ascii=False, separators=(",", ":")
                ),
            },
        ],
        "response_format": _RESPONSE_FORMAT,
        "provider": {"require_parameters": True},
    }

    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            response = client.post(
                _OPENROUTER_URL,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
    except httpx.TimeoutException:
        logger.warning("OpenRouter revision summary request timed out")
        return None
    except httpx.HTTPError:
        logger.warning("OpenRouter revision summary request failed")
        return None

    if response.status_code != 200:
        logger.warning(
            "OpenRouter revision summary returned status %s", response.status_code
        )
        return None

    try:
        payload = response.json()
    except ValueError:
        logger.warning("OpenRouter revision summary returned invalid JSON")
        return None

    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None

    summary = _parse_summary(message.get("content"))
    if summary is None:
        logger.warning("OpenRouter revision summary failed schema validation")
    return summary
