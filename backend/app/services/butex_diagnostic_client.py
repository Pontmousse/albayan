"""Thin dev diagnostic adapter for BuTeX's real MathObject editor bridge."""

from __future__ import annotations

from typing import Any, Mapping

from fastapi import HTTPException

from app.services import butex_worker_client


def diagnose_math_object(math_object: Mapping[str, Any]) -> dict[str, Any]:
    """Ask the BuTeX worker whether this stored MathObject can reopen in the editor.

    The worker implementation calls BuTeX's existing ``fromMathObjectJson`` and
    ``mathObjectToEditorSession`` functions. This host adapter intentionally does
    not reproduce any equation parsing/editor rules.
    """
    payload = butex_worker_client._post(  # noqa: SLF001 - same trusted worker boundary
        "/v1/document2/diagnostics/math-object",
        {"math_object": dict(math_object)},
    )
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise HTTPException(status_code=502, detail="استجابة تشخيص BuTeX غير صالحة.")
    diagnostic = payload.get("math_diagnostic")
    if not isinstance(diagnostic, dict) or not isinstance(diagnostic.get("ok"), bool):
        raise HTTPException(status_code=502, detail="استجابة تشخيص BuTeX غير صالحة.")

    stage = diagnostic.get("stage")
    editable = diagnostic.get("editable")
    if stage not in {"fromMathObjectJson", "mathObjectToEditorSession"} or not isinstance(
        editable, bool
    ):
        raise HTTPException(status_code=502, detail="استجابة تشخيص BuTeX غير صالحة.")

    result: dict[str, Any] = {
        "ok": diagnostic["ok"],
        "stage": stage,
        "editable": editable,
    }
    if diagnostic["ok"]:
        for key in ("english_latex", "arabic_latex"):
            value = diagnostic.get(key)
            if isinstance(value, str):
                result[key] = value[:20_000]
    else:
        error = diagnostic.get("error")
        result["error"] = error[:1000] if isinstance(error, str) else "BuTeX editor import failed"
    return result
