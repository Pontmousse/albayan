"""Dev-only, non-persistent inspection of the real equation pipeline."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import HTTPException

from app.core.tracing import current_trace_id
from app.services import (
    burhan_client,
    burhan_reverse_client,
    butex_diagnostic_client,
    butex_worker_client,
)


def _stage(
    *,
    available: bool,
    ok: bool | None,
    authoritative: bool,
    data: Any | None = None,
    error: Any | None = None,
    reason: str | None = None,
    human_action: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": available,
        "ok": ok,
        "authoritative": authoritative,
    }
    if data is not None:
        result["data"] = data
    if error is not None:
        result["error"] = error
    if reason is not None:
        result["reason"] = reason
    if human_action is not None:
        result["human_action"] = human_action
    return result


def _bounded_error(exc: HTTPException) -> dict[str, Any]:
    detail = exc.detail
    if isinstance(detail, dict):
        return {
            key: value[:1000] if isinstance(value, str) else value
            for key, value in detail.items()
            if key in {"code", "message", "error_code"}
            and isinstance(value, (str, int, float, bool, type(None)))
        } or {"message": "Diagnostic stage failed"}
    return {"message": str(detail)[:1000]}


def _unavailable_from_http(exc: HTTPException) -> tuple[bool, str | None]:
    detail = exc.detail
    code = detail.get("code") if isinstance(detail, dict) else None
    unavailable = exc.status_code in {404, 503} or code in {
        "burhan_unavailable",
        "not_found",
    }
    if not unavailable:
        return False, None
    if code == "burhan_unavailable" or exc.status_code == 503:
        return True, "Configure the development Burhan/BuTeX service required by this stage."
    return True, "Deploy a BuTeX worker revision that exposes the headless MathObject diagnostic endpoint."


def _missing_downstream(reason: str, human_action: str) -> dict[str, Any]:
    return _stage(
        available=False,
        ok=None,
        authoritative=True,
        reason=reason,
        human_action=human_action,
    )


def _extract_field_id(document: dict[str, Any]) -> str:
    blocks = document.get("blocks")
    if not isinstance(blocks, list) or not blocks or not isinstance(blocks[0], dict):
        raise HTTPException(status_code=502, detail="Document2 worker did not create a paragraph block.")
    inline_ids = blocks[0].get("inline_ids")
    if not isinstance(inline_ids, dict) or not isinstance(inline_ids.get("field_id"), str):
        raise HTTPException(status_code=502, detail="Document2 worker did not expose a paragraph field id.")
    return inline_ids["field_id"]


def inspect_equation(
    *,
    latex: str,
    display: bool,
    model_tier: str,
) -> dict[str, Any]:
    """Run one equation through every deterministic stage currently observable.

    This function writes no article/database state. The temporary Document2
    value exists only in memory and is sent to the stateless BuTeX worker.
    """
    report: dict[str, Any] = {
        "trace_id": current_trace_id(),
        "model_tier": model_tier,
        "display": display,
        "stages": {
            "canonical_input": _stage(
                available=True,
                ok=True,
                authoritative=True,
                data={"latex": latex, "display": display},
            )
        },
    }
    stages = report["stages"]

    raw: dict[str, Any] = {}
    try:
        token, mappings = burhan_client.convert_latex_to_math_token(
            latex,
            display=display,
            label=None,
            mappings={},
            model_tier=model_tier,
            diagnostics=raw,
        )
    except HTTPException as exc:
        unavailable, human_action = _unavailable_from_http(exc)
        stages["burhan_conversion"] = _stage(
            available=not unavailable,
            ok=None if unavailable else False,
            authoritative=True,
            error=_bounded_error(exc),
            reason="burhan_stage_unavailable" if unavailable else "burhan_conversion_failed",
            human_action=human_action,
        )
        action = human_action or "Resolve the Burhan conversion failure before inspecting downstream stages."
        for name in (
            "albayan_projection",
            "document2_command",
            "headless_butex_validation",
            "reverse_conversion",
        ):
            stages[name] = _missing_downstream("blocked_by_burhan", action)
        stages["browser_validation"] = _stage(
            available=False,
            ok=None,
            authoritative=False,
            reason="separate_playwright_observation_plane",
            human_action="Use Playwright MCP for real browser/editor/render validation when available.",
        )
        report["ok"] = False
        report["partial"] = True
        return report

    stages["canonical_input"] = _stage(
        available=True,
        ok=True,
        authoritative=True,
        data=raw.get("canonical_input", {"latex": latex, "display": display}),
    )
    stages["burhan_conversion"] = _stage(
        available=True,
        ok=True,
        authoritative=True,
        data={
            "request": raw.get("burhan_request"),
            "english_json": raw.get("english_json"),
            "arabic_json": raw.get("arabic_json"),
            "arabic_latex": raw.get("arabic_latex"),
            "mappings": raw.get("mappings", mappings),
            "warnings": raw.get("warnings", []),
            "resolved_model": raw.get("resolved_model"),
            "duration_ms": raw.get("duration_ms"),
        },
    )

    math_object = token["math_object"]
    stages["albayan_projection"] = _stage(
        available=True,
        ok=True,
        authoritative=True,
        data={
            "token": token,
            "editor_math_object": math_object,
        },
    )

    document2_ok = False
    try:
        document = butex_worker_client.normalize_document(
            {"node_type": "DocumentObject", "blocks": []}
        )
        document = butex_worker_client.apply_document_command(
            document,
            {
                "op": "insert_text_block",
                "kind": "paragraph",
                "text": "",
                "anchor": {"end": True},
                "metadata": {"source": "agent"},
            },
        )
        field_id = _extract_field_id(document)
        command = {
            "op": "insert_inline_token",
            "field_id": field_id,
            "token": token,
            "anchor": {"end": True},
        }
        result_document = butex_worker_client.apply_document_command(document, command)
        stages["document2_command"] = _stage(
            available=True,
            ok=True,
            authoritative=True,
            data={
                "command": command,
                "result_document": result_document,
            },
        )
        document2_ok = True
    except HTTPException as exc:
        unavailable, human_action = _unavailable_from_http(exc)
        stages["document2_command"] = _stage(
            available=not unavailable,
            ok=None if unavailable else False,
            authoritative=True,
            error=_bounded_error(exc),
            reason="document2_worker_unavailable" if unavailable else "document2_command_failed",
            human_action=human_action,
        )

    headless_ok = False
    try:
        diagnostic = butex_diagnostic_client.diagnose_math_object(math_object)
        headless_ok = diagnostic.get("ok") is True
        stages["headless_butex_validation"] = _stage(
            available=True,
            ok=headless_ok,
            authoritative=True,
            data=diagnostic,
            error=None if headless_ok else {"message": diagnostic.get("error", "BuTeX editor import failed")},
        )
    except HTTPException as exc:
        unavailable, human_action = _unavailable_from_http(exc)
        stages["headless_butex_validation"] = _stage(
            available=not unavailable,
            ok=None if unavailable else False,
            authoritative=True,
            error=_bounded_error(exc),
            reason="headless_butex_unavailable" if unavailable else "headless_butex_failed",
            human_action=human_action,
        )

    reverse_ok = False
    reverse_started = perf_counter()
    try:
        reverse_latex, reverse_warnings = burhan_reverse_client.convert_math_object_to_english(
            math_object,
            variable_mapping=mappings,
            model_tier=model_tier,
        )
        stages["reverse_conversion"] = _stage(
            available=True,
            ok=True,
            authoritative=True,
            data={
                "canonical_latex": reverse_latex,
                "warnings": reverse_warnings,
                "duration_ms": round((perf_counter() - reverse_started) * 1000, 3),
            },
        )
        reverse_ok = True
    except HTTPException as exc:
        unavailable, human_action = _unavailable_from_http(exc)
        stages["reverse_conversion"] = _stage(
            available=not unavailable,
            ok=None if unavailable else False,
            authoritative=True,
            error=_bounded_error(exc),
            reason="reverse_conversion_unavailable" if unavailable else "reverse_conversion_failed",
            human_action=human_action,
        )

    stages["browser_validation"] = _stage(
        available=False,
        ok=None,
        authoritative=False,
        reason="separate_playwright_observation_plane",
        human_action="Use Playwright MCP for real browser/editor/render validation; Dev MCP does not proxy browser control.",
    )

    report["ok"] = document2_ok and headless_ok and reverse_ok
    report["partial"] = any(
        stage.get("available") is False
        for name, stage in stages.items()
        if name != "browser_validation"
    )
    return report
