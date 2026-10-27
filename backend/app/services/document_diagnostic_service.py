from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.core.tracing import current_trace_id
from app.services import butex_diagnostic_client, butex_worker_client

_WORKER_UNAVAILABLE = {401, 403, 404, 502, 503, 504}


def _failure(operation: str, exc: HTTPException) -> dict[str, Any]:
    detail = exc.detail
    if isinstance(detail, dict):
        error = {
            key: value[:500] if isinstance(value, str) else value
            for key, value in detail.items()
            if key in {"code", "message", "error_code"}
            and isinstance(value, (str, int, bool))
        }
    else:
        error = {"code": "worker_error", "message": str(detail)[:500]}
    blocked = exc.status_code in _WORKER_UNAVAILABLE
    return {
        "ok": False,
        "status": "blocked" if blocked else "failed",
        "operation": operation,
        "stage": "butex_worker",
        "trace_id": current_trace_id(),
        "status_code": exc.status_code,
        "error": error,
        "human_action": (
            "Verify the authenticated development BuTeX worker route and deployed source revision."
            if blocked else None
        ),
    }


def inspect_document(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    document = payload.get("document")
    try:
        if operation == "diagnose_contract":
            response = butex_worker_client._post(
                "/v1/document/diagnostics/contract", {}
            )
            if not isinstance(response, dict) or response.get("ok") is not True:
                raise HTTPException(status_code=502, detail="Invalid worker contract diagnostic")
            result = response.get("contract")
            if not isinstance(result, dict) or not isinstance(result.get("routes"), dict):
                raise HTTPException(status_code=502, detail="Invalid worker contract")
        else:
            if operation in {
                "normalize", "outline", "references", "reference_index",
                "export", "apply_command",
            } and not isinstance(document, dict):
                raise HTTPException(status_code=422, detail="Document fixture is required")
            if operation == "normalize":
                result = butex_worker_client.normalize_document(document)
            elif operation == "outline":
                result = butex_worker_client.outline_document(document)
            elif operation == "references":
                result = butex_worker_client.reference_document(document)
            elif operation == "reference_index":
                result = butex_worker_client.reference_index_document(document)
            elif operation == "export":
                latex, asset_ids = butex_worker_client.export_document(document)
                result = {"latex": latex, "asset_ids": asset_ids}
            elif operation == "apply_command":
                command = payload.get("command")
                if not isinstance(command, dict):
                    raise HTTPException(status_code=422, detail="Command fixture is required")
                result = butex_worker_client.apply_document_command(document, command)
            elif operation == "diff":
                before, after = payload.get("before"), payload.get("after")
                if not isinstance(before, dict) or not isinstance(after, dict):
                    raise HTTPException(status_code=422, detail="Two document fixtures are required")
                result = butex_worker_client.diff_documents(before, after)
            elif operation == "diagnose_math_object":
                math = payload.get("math_object")
                if not isinstance(math, dict):
                    raise HTTPException(status_code=422, detail="MathObject fixture is required")
                result = butex_diagnostic_client.diagnose_math_object(math)
            elif operation == "project_math_object_english":
                math = payload.get("math_object")
                if not isinstance(math, dict):
                    raise HTTPException(status_code=422, detail="MathObject fixture is required")
                result = butex_worker_client.project_math_object_to_english(math)
            else:
                raise HTTPException(status_code=422, detail="Unsupported diagnostic operation")
        return {
            "ok": True,
            "status": "passed",
            "operation": operation,
            "stage": "butex_worker",
            "trace_id": current_trace_id(),
            "data": result,
        }
    except HTTPException as exc:
        return _failure(operation, exc)
