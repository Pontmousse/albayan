"""Small trusted client for Burhan equation conversion."""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections.abc import Mapping
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.document2 import DocumentMathObjectJson

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 45.0
_SUPPORTED_ENVIRONMENTS = (
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
    "equation",
    "equation*",
)

_UNCONFIGURED = HTTPException(
    status_code=503,
    detail={"code": "burhan_unavailable", "message": "خدمة تحويل المعادلات غير مهيأة."},
)


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _split_latex(latex: str, *, display: bool) -> tuple[str, str, str, str]:
    value = latex.strip()
    if not value:
        raise _error(422, "invalid_math_latex", "نص المعادلة فارغ.")

    wrappers: list[tuple[str, str, bool]] = [
        ("$$", "$$", True),
        (r"\[", r"\]", True),
        (r"\(", r"\)", False),
        ("$", "$", False),
    ]
    wrappers.extend(
        (rf"\begin{{{name}}}", rf"\end{{{name}}}", True)
        for name in _SUPPORTED_ENVIRONMENTS
    )

    for opening, closing, wrapper_display in wrappers:
        if value.startswith(opening) and value.endswith(closing):
            if wrapper_display != display:
                raise _error(
                    422,
                    "math_display_mismatch",
                    "نوع المعادلة لا يطابق محددات LaTeX المرسلة.",
                )
            inner = value[len(opening) : len(value) - len(closing)].strip()
            if not inner:
                raise _error(422, "invalid_math_latex", "محتوى المعادلة فارغ.")
            return value, opening, inner, closing

    # Reject obvious unmatched top-level delimiters instead of nesting them.
    if value.startswith(("$", r"\(", r"\[", r"\begin{")):
        raise _error(422, "invalid_math_latex", "محددات LaTeX للمعادلة غير مكتملة.")

    opening, closing = (r"\[", r"\]") if display else ("$", "$")
    return opening + value + closing, opening, value, closing


def _validated_mappings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")
    mappings: dict[str, str] = {}
    for english, arabic in value.items():
        if (
            not isinstance(english, str)
            or not english.strip()
            or not isinstance(arabic, str)
            or not arabic.strip()
        ):
            raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")
        mappings[english] = arabic
    return mappings


def _segment_mapping_keys(expr: str, mappings: Mapping[str, str]) -> list[str] | None:
    """Find a deterministic full segmentation, preferring longer mapping keys."""
    keys = sorted((key for key in mappings if key), key=lambda key: (-len(key), key))
    memo: dict[int, list[str] | None] = {}

    def solve(offset: int) -> list[str] | None:
        if offset == len(expr):
            return []
        if offset in memo:
            return memo[offset]
        for key in keys:
            if expr.startswith(key, offset):
                remainder = solve(offset + len(key))
                if remainder is not None:
                    memo[offset] = [key, *remainder]
                    return memo[offset]
        memo[offset] = None
        return None

    return solve(0)


def _arabic_char_expr(expr: str, mappings: Mapping[str, str]) -> str:
    direct = mappings.get(expr)
    if direct is not None:
        return direct

    parts = _segment_mapping_keys(expr, mappings)
    if parts:
        return "".join(mappings[part] for part in reversed(parts))

    # Non-Latin values are already safe to preserve in the editor-shaped tree.
    if not re.search(r"[A-Za-z]", expr):
        return expr
    raise _error(
        502,
        "invalid_burhan_response",
        "تعذّر مطابقة متغيرات المعادلة مع تحويل Burhan.",
    )


def _editor_math_object(
    english_json: str,
    mappings: Mapping[str, str],
    *,
    display: bool,
    label: str | None,
) -> dict[str, Any]:
    try:
        tree = json.loads(english_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.") from exc
    if not isinstance(tree, dict) or tree.get("node_type") != "MathObject":
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("node_type") == "CharObject":
                expr = value.get("expr")
                if not isinstance(expr, str):
                    raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")
                value["expr"] = _arabic_char_expr(expr, mappings)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(tree)
    tree["source_side"] = "arabic"
    tree["source_owner"] = "editor"
    if display and label is not None and label.strip():
        tree["label_enabled"] = True
        tree["label"] = label.strip()

    try:
        return DocumentMathObjectJson.model_validate(tree).model_dump(exclude_unset=True)
    except Exception as exc:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير متوافقة.") from exc


def convert_latex_to_math_token(
    latex: str,
    *,
    display: bool,
    label: str | None,
    mappings: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Convert normal English LaTeX into the strict editor-shaped Document2 math token."""
    base = settings.burhan_url.rstrip("/")
    if not base:
        raise _UNCONFIGURED

    full_match, opening, inner_content, closing = _split_latex(latex, display=display)
    payload = {
        "run_id": str(uuid.uuid4()),
        "full_match": full_match,
        "opening": opening,
        "inner_content": inner_content,
        "closing": closing,
        "context": inner_content,
        "mappings": dict(mappings),
        "mapping_instructions": None,
        "digits_mapping": "digits",
        "model_tier": settings.burhan_model_tier,
        "prescanning": True,
    }

    try:
        with httpx.Client(base_url=base, timeout=_TIMEOUT_SECONDS) as client:
            response = client.post("/convert", json=payload)
    except httpx.TimeoutException as exc:
        logger.warning("Burhan equation conversion timed out")
        raise _error(504, "burhan_timeout", "انتهت مهلة تحويل المعادلة.") from exc
    except httpx.HTTPError as exc:
        logger.warning("Burhan equation conversion request failed")
        raise _error(502, "burhan_unavailable", "تعذّر الاتصال بخدمة تحويل المعادلات.") from exc

    if response.status_code == 422:
        raise _error(422, "invalid_math_latex", "تعذّر فهم صيغة LaTeX للمعادلة.")
    if response.status_code != 200:
        raise _error(502, "burhan_unavailable", "تعذّر تحويل المعادلة.")
    try:
        body = response.json()
    except ValueError as exc:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.") from exc
    if not isinstance(body, dict) or body.get("status") != "ok":
        raise _error(502, "invalid_burhan_response", "لم تكتمل عملية تحويل المعادلة.")

    arabic_source = body.get("arabic")
    english_json = body.get("english_json")
    resolved_mappings = _validated_mappings(body.get("mappings"))
    if not isinstance(arabic_source, str) or not arabic_source.strip() or not isinstance(english_json, str):
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    math_object = _editor_math_object(
        english_json,
        resolved_mappings,
        display=display,
        label=label,
    )
    return {
        "kind": "math",
        "source": arabic_source,
        "math_object": math_object,
    }, resolved_mappings
