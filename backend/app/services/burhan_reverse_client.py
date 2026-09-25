"""Trusted read-only client for Burhan's English projection endpoint."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.services.burhan_client import _burhan_headers, _resolve_model_tier

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 45.0
_DOCUMENT2_ROOT_METADATA = {
    "source_side",
    "source_owner",
    "label_enabled",
    "label",
}


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _compact_warnings(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")
    compact: list[str] = []
    for warning in value:
        text: str | None = None
        if isinstance(warning, str) and warning.strip():
            text = warning.strip()
        elif isinstance(warning, dict):
            code = warning.get("code")
            message = warning.get("message")
            if isinstance(code, str) and code.strip():
                text = code.strip()
            elif isinstance(message, str) and message.strip():
                text = message.strip()
        if text is not None and text not in compact:
            compact.append(text[:1000])
    return compact[:50]


def _strip_outer_math_delimiters(latex: str) -> str:
    value = latex.strip()
    for opening, closing in (
        ("$$", "$$"),
        (r"\[", r"\]"),
        (r"\(", r"\)"),
        ("$", "$"),
    ):
        if value.startswith(opening) and value.endswith(closing):
            return value[len(opening) : len(value) - len(closing)].strip()
    return value


def convert_math_object_to_english(
    math_object: Mapping[str, Any],
    *,
    variable_mapping: Mapping[str, str],
    model_tier: str | None = None,
) -> tuple[str, list[str]]:
    """Project one canonical Document2 MathObject to normal English LaTeX."""
    base = settings.burhan_url.rstrip("/")
    if not base:
        raise _error(503, "burhan_unavailable", "خدمة تحويل المعادلات غير مهيأة.")

    tree = deepcopy(dict(math_object))
    if tree.get("node_type") != "MathObject":
        raise _error(422, "invalid_math_object", "بنية المعادلة المخزنة غير صالحة.")
    for key in _DOCUMENT2_ROOT_METADATA:
        tree.pop(key, None)

    payload = {
        "run_id": str(uuid.uuid4()),
        "english_json": json.dumps(tree, ensure_ascii=False),
        "variable_mapping": dict(variable_mapping),
        "model_tier": _resolve_model_tier(model_tier),
    }

    try:
        with httpx.Client(
            base_url=base,
            timeout=_TIMEOUT_SECONDS,
            headers=_burhan_headers(),
        ) as client:
            response = client.post("/convert-to-english", json=payload)
    except httpx.TimeoutException as exc:
        logger.warning("Burhan English equation projection timed out")
        raise _error(504, "burhan_timeout", "انتهت مهلة قراءة المعادلة.") from exc
    except httpx.HTTPError as exc:
        logger.warning("Burhan English equation projection request failed")
        raise _error(502, "burhan_unavailable", "تعذّر الاتصال بخدمة تحويل المعادلات.") from exc

    if response.status_code == 422:
        raise _error(
            502,
            "burhan_reverse_unsupported",
            "تعذّر تحويل بنية المعادلة المخزنة إلى الصيغة الإنجليزية.",
        )
    if response.status_code != 200:
        raise _error(502, "burhan_unavailable", "تعذّر قراءة المعادلة عبر Burhan.")

    try:
        body = response.json()
    except ValueError as exc:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.") from exc
    if not isinstance(body, dict) or body.get("status") != "ok":
        raise _error(502, "invalid_burhan_response", "لم تكتمل عملية قراءة المعادلة.")

    english_latex = body.get("english_latex")
    if not isinstance(english_latex, str) or not english_latex.strip():
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    return _strip_outer_math_delimiters(english_latex), _compact_warnings(
        body.get("warnings", [])
    )
