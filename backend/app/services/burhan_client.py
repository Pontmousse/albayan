"""Small trusted client for Burhan equation conversion."""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Mapping
from time import perf_counter
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.tracing import emit_trace_event, trace_headers
from app.schemas.document2 import DocumentMathObjectJson

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 45.0
# Canonical equation interoperability is an operation-level policy: always use
# Burhan's deterministic heuristic tier, never the ambient settings default or
# an authentication accident.
CANONICAL_INTEROP_TIER = "heuristic"
_SUPPORTED_MODEL_TIERS = {"heuristic", "free", "cheap", "medium", "frontier"}
# Genuine outer math wrappers only. Math-only inner environments (pmatrix,
# array, aligned, …) are equation content and must not appear here.
_OUTER_MATH_WRAPPER_ENVIRONMENTS = (
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


def _burhan_headers() -> dict[str, str]:
    """Return trusted machine headers plus the current diagnostic correlation ID."""
    headers = trace_headers()
    api_key = os.getenv("BURHAN_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _resolve_model_tier(model_tier: str | None) -> str:
    value = (model_tier or settings.burhan_model_tier).strip().lower()
    if value not in _SUPPORTED_MODEL_TIERS:
        raise _error(422, "invalid_model_tier", "مستوى نموذج Burhan غير مدعوم.")
    return value


def _is_incomplete_outer_wrapper(value: str) -> bool:
    """True when input starts an outer math wrapper but is not a complete one.

    Distinguishes genuine outer wrappers ($...$, \\[...\\], equation/align, …)
    from math-only inner environments (pmatrix, array, aligned, …), which are
    equation content and must not be treated as incomplete delimiters.
    """
    if value.startswith(("$", r"\(", r"\[")):
        return True
    return any(
        value.startswith(rf"\begin{{{name}}}")
        for name in _OUTER_MATH_WRAPPER_ENVIRONMENTS
    )


def _split_latex(latex: str, *, display: bool) -> tuple[str, str, str, str]:
    value = latex.strip()
    if not value:
        raise _error(422, "invalid_math_latex", "نص المعادلة فارغ.")

    # Only genuine outer math wrappers — never math-only inner environments.
    wrappers: list[tuple[str, str, bool]] = [
        ("$$", "$$", True),
        (r"\[", r"\]", True),
        (r"\(", r"\)", False),
        ("$", "$", False),
    ]
    wrappers.extend(
        (rf"\begin{{{name}}}", rf"\end{{{name}}}", True)
        for name in _OUTER_MATH_WRAPPER_ENVIRONMENTS
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

    if _is_incomplete_outer_wrapper(value):
        raise _error(422, "invalid_math_latex", "محددات LaTeX للمعادلة غير مكتملة.")

    # No outer wrapper: treat the full string as canonical equation content and
    # wrap from the explicit display flag (inner envs like pmatrix stay intact).
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


def _drop_burhan_internal_math_metadata(value: Any) -> None:
    """Remove Burhan-only annotations that are not part of the Document2 wire AST."""
    if isinstance(value, dict):
        value.pop("arabic_unit", None)
        for child in value.values():
            _drop_burhan_internal_math_metadata(child)
    elif isinstance(value, list):
        for child in value:
            _drop_burhan_internal_math_metadata(child)


def _arabic_math_object(
    arabic_json: Any,
    *,
    display: bool,
    label: str | None,
) -> dict[str, Any]:
    """Validate Burhan's Arabic MathObject without rewriting its mathematical AST."""
    if isinstance(arabic_json, str):
        try:
            tree = json.loads(arabic_json)
        except json.JSONDecodeError as exc:
            raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.") from exc
    elif isinstance(arabic_json, dict):
        tree = dict(arabic_json)
    else:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    if tree.get("node_type") != "MathObject":
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    # Burhan's BaseNode includes root script placeholders; Document2 MathObject does not.
    tree.pop("superscript", None)
    tree.pop("subscript", None)
    _drop_burhan_internal_math_metadata(tree)
    tree["source_side"] = "arabic"
    tree["source_owner"] = "editor"
    if display and label is not None and label.strip():
        tree["label_enabled"] = True
        tree["label"] = label.strip()

    try:
        return DocumentMathObjectJson.model_validate(tree).model_dump(exclude_unset=True)
    except Exception as exc:
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير متوافقة.") from exc


def _decode_json_stage(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value[:20_000]


def _bounded_warnings(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    compact: list[Any] = []
    for item in value[:50]:
        if isinstance(item, str):
            compact.append(item[:1000])
        elif isinstance(item, dict):
            compact.append(
                {
                    key: raw[:1000] if isinstance(raw, str) else raw
                    for key, raw in item.items()
                    if key in {"code", "message", "stage"}
                    and isinstance(raw, (str, int, float, bool, type(None)))
                }
            )
    return compact


def normalize_english_math_ast(value: Any) -> Any:
    """Normalize an English MathObject/AST for semantic equivalence comparison.

    Drops null placeholders and sorts object keys so formatting-only differences
    (for example `x_1` vs `x_{1}` once both are parsed) do not produce false
    failures. Structural/operator/variable identity is preserved.
    """
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            child = value[key]
            if child is None:
                continue
            normalized[key] = normalize_english_math_ast(child)
        return normalized
    if isinstance(value, list):
        return [normalize_english_math_ast(child) for child in value]
    return value


def convert_latex_to_math_token(
    latex: str,
    *,
    display: bool,
    label: str | None,
    mappings: Mapping[str, str],
    model_tier: str | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Convert canonical English LaTeX into a structured Arabic Document2 math token."""
    base = settings.burhan_url.rstrip("/")
    if not base:
        raise _UNCONFIGURED

    tier = _resolve_model_tier(model_tier)
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
        "model_tier": tier,
        "prescanning": True,
    }

    if diagnostics is not None:
        diagnostics.update(
            {
                "canonical_input": {
                    "latex": latex,
                    "full_match": full_match,
                    "opening": opening,
                    "inner_content": inner_content,
                    "closing": closing,
                    "display": display,
                },
                "burhan_request": {
                    "model_tier": tier,
                    "digits_mapping": "digits",
                    "prescanning": True,
                    "mapping_count": len(mappings),
                },
            }
        )

    started = perf_counter()
    emit_trace_event(
        service="albayan-backend",
        stage="burhan.convert",
        status="started",
        model_tier=tier,
    )
    try:
        with httpx.Client(
            base_url=base,
            timeout=_TIMEOUT_SECONDS,
            headers=_burhan_headers(),
        ) as client:
            response = client.post("/convert", json=payload)
    except httpx.TimeoutException as exc:
        emit_trace_event(
            service="albayan-backend",
            stage="burhan.convert",
            status="timeout",
            duration_ms=(perf_counter() - started) * 1000,
        )
        logger.warning("Burhan equation conversion timed out")
        raise _error(504, "burhan_timeout", "انتهت مهلة تحويل المعادلة.") from exc
    except httpx.HTTPError as exc:
        emit_trace_event(
            service="albayan-backend",
            stage="burhan.convert",
            status="unreachable",
            duration_ms=(perf_counter() - started) * 1000,
            error_type=type(exc).__name__,
        )
        logger.warning("Burhan equation conversion request failed")
        raise _error(502, "burhan_unavailable", "تعذّر الاتصال بخدمة تحويل المعادلات.") from exc

    duration_ms = (perf_counter() - started) * 1000
    emit_trace_event(
        service="albayan-backend",
        stage="burhan.convert",
        status="ok" if response.status_code == 200 else "error",
        duration_ms=duration_ms,
        status_code=response.status_code,
    )
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
    resolved_mappings = _validated_mappings(body.get("mappings"))
    if not isinstance(arabic_source, str) or not arabic_source.strip():
        raise _error(502, "invalid_burhan_response", "استجابة خدمة تحويل المعادلات غير صالحة.")

    math_object = _arabic_math_object(
        body.get("arabic_json"),
        display=display,
        label=label,
    )
    if diagnostics is not None:
        diagnostics.update(
            {
                "duration_ms": round(duration_ms, 3),
                "english_json": _decode_json_stage(body.get("english_json")),
                "arabic_json": _decode_json_stage(body.get("arabic_json")),
                "arabic_latex": arabic_source,
                "mappings": dict(resolved_mappings),
                "warnings": _bounded_warnings(body.get("warnings")),
                "resolved_model": body.get("resolved_model")
                if isinstance(body.get("resolved_model"), str)
                else None,
                "editor_math_object": math_object,
            }
        )
    return {
        "kind": "math",
        "source": arabic_source,
        "math_object": math_object,
    }, resolved_mappings


def convert_canonical_latex_to_math_object(
    latex: str,
    *,
    display: bool,
    label: str | None,
    mappings: Mapping[str, str],
    diagnostics: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Deterministic canonical → Document2 conversion for interoperability paths."""
    return convert_latex_to_math_token(
        latex,
        display=display,
        label=label,
        mappings=mappings,
        model_tier=CANONICAL_INTEROP_TIER,
        diagnostics=diagnostics,
    )
