"""Private client for the BuTeX document worker."""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.tracing import TRACE_HEADER, current_trace_id, emit_trace_event

logger = logging.getLogger(__name__)

_MAX_BODY_BYTES = 5 * 1024 * 1024
_TIMEOUT_SECONDS = 15.0
_EXPECTED_WORKER_STATUSES = {400, 401, 404, 413, 422}
_DIFF_KINDS = {"added", "removed", "context"}
_MAX_DIFF_CHUNKS = 500
_MAX_DIFF_CHUNK_CHARS = 20_000

_UNCONFIGURED = HTTPException(
    status_code=503,
    detail="عامل BuTeX غير مُهيّأ على الخادم.",
)


def _request_id() -> str:
    # Reuse the correlation ID when a request context exists without making it
    # an authorization primitive. Keep the historical fallback for offline calls.
    return current_trace_id() or "albayan-backend"


def _invalid_response() -> HTTPException:
    return HTTPException(
        status_code=502,
        detail="استجابة عامل BuTeX غير صالحة.",
    )


def _json_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())


def _worker_error(response: httpx.Response) -> HTTPException:
    try:
        payload = response.json()
    except ValueError:
        return _invalid_response()

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = error.get("code")
        message = error.get("message")
        if isinstance(code, str) and isinstance(message, str):
            detail: dict[str, Any] = {
                "code": code[:100],
                "message": message[:2000],
            }
            raw_issues = error.get("issues")
            if isinstance(raw_issues, list):
                issues: list[dict[str, str]] = []
                for raw_issue in raw_issues[:100]:
                    if not isinstance(raw_issue, dict):
                        continue
                    issue = {
                        key: value[:500]
                        for key in ("code", "path", "blockId", "tokenId")
                        if isinstance((value := raw_issue.get(key)), str)
                    }
                    if "code" in issue:
                        issues.append(issue)
                if issues:
                    detail["issues"] = issues
            status = (
                response.status_code
                if response.status_code in _EXPECTED_WORKER_STATUSES
                else 502
            )
            return HTTPException(
                status_code=status,
                detail=detail,
            )

    return _invalid_response()


def _require_success_document(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    document = payload.get("document")
    if not isinstance(document, dict):
        raise _invalid_response()
    return document


def _require_success_outline(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    outline = payload.get("outline")
    if not isinstance(outline, list) or not all(
        isinstance(row, dict) for row in outline
    ):
        raise _invalid_response()
    return outline


def _require_success_references(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    references = payload.get("references")
    if not isinstance(references, list) or not all(
        isinstance(reference, dict) for reference in references
    ):
        raise _invalid_response()
    return references


def _require_success_reference_index(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    reference_index = payload.get("reference_index")
    if not isinstance(reference_index, dict):
        raise _invalid_response()
    for key in ("citations", "cross_references", "labels"):
        rows = reference_index.get(key)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise _invalid_response()
    unresolved = reference_index.get("unresolved")
    if not isinstance(unresolved, dict):
        raise _invalid_response()
    for key in ("citation_keys", "cross_reference_keys"):
        values = unresolved.get(key)
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise _invalid_response()
    return reference_index


def _require_success_export(payload: Any) -> tuple[str, list[str]]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    latex = payload.get("latex")
    asset_ids = payload.get("asset_ids")
    if not isinstance(latex, str) or not latex:
        raise _invalid_response()
    if not isinstance(asset_ids, list) or not all(
        isinstance(asset_id, str) and bool(asset_id.strip())
        for asset_id in asset_ids
    ):
        raise _invalid_response()
    if len(set(asset_ids)) != len(asset_ids):
        raise _invalid_response()
    return latex, asset_ids


def _require_success_diff(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise _invalid_response()
    diff = payload.get("diff")
    if not isinstance(diff, dict):
        raise _invalid_response()
    if diff.get("version") != 1:
        raise _invalid_response()
    changed = diff.get("changed")
    truncated = diff.get("truncated")
    chunks = diff.get("chunks")
    if not isinstance(changed, bool) or not isinstance(truncated, bool):
        raise _invalid_response()
    if not isinstance(chunks, list) or len(chunks) > _MAX_DIFF_CHUNKS:
        raise _invalid_response()

    validated_chunks: list[dict[str, str]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict) or set(chunk) != {"kind", "text"}:
            raise _invalid_response()
        kind = chunk.get("kind")
        text = chunk.get("text")
        if kind not in _DIFF_KINDS:
            raise _invalid_response()
        if (
            not isinstance(text, str)
            or not text
            or len(text) > _MAX_DIFF_CHUNK_CHARS
        ):
            raise _invalid_response()
        validated_chunks.append({"kind": kind, "text": text})

    if changed is False and validated_chunks:
        raise _invalid_response()
    return {
        "version": 1,
        "changed": changed,
        "truncated": truncated,
        "chunks": validated_chunks,
    }


def _post(path: str, payload: dict[str, Any]) -> Any:
    base = settings.butex_worker_url.rstrip("/")
    token = settings.butex_worker_token.strip()
    if not base or not token:
        raise _UNCONFIGURED

    if _json_size(payload) > _MAX_BODY_BYTES:
        raise HTTPException(
            status_code=413,
            detail="حجم طلب المستند يتجاوز الحد المسموح.",
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Request-ID": _request_id(),
    }
    trace_id = current_trace_id()
    if trace_id:
        headers[TRACE_HEADER] = trace_id

    started = perf_counter()
    emit_trace_event(
        service="albayan-backend",
        stage="butex_worker.request",
        status="started",
        path=path,
    )
    try:
        with httpx.Client(base_url=base, timeout=_TIMEOUT_SECONDS) as client:
            response = client.post(
                path,
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        emit_trace_event(
            service="albayan-backend",
            stage="butex_worker.request",
            status="timeout",
            duration_ms=(perf_counter() - started) * 1000,
            path=path,
        )
        logger.warning("BuTeX worker request timed out: %s", path)
        raise HTTPException(status_code=504, detail="انتهت مهلة عامل BuTeX.") from exc
    except httpx.HTTPError as exc:
        emit_trace_event(
            service="albayan-backend",
            stage="butex_worker.request",
            status="unreachable",
            duration_ms=(perf_counter() - started) * 1000,
            path=path,
            error_type=type(exc).__name__,
        )
        logger.warning("BuTeX worker request failed: %s", path)
        raise HTTPException(status_code=502, detail="تعذّر الاتصال بعامل BuTeX.") from exc

    emit_trace_event(
        service="albayan-backend",
        stage="butex_worker.request",
        status="ok" if response.status_code == 200 else "error",
        duration_ms=(perf_counter() - started) * 1000,
        path=path,
        status_code=response.status_code,
    )
    if response.status_code != 200:
        raise _worker_error(response)

    try:
        return response.json()
    except ValueError as exc:
        raise _invalid_response() from exc


def normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    return _require_success_document(
        _post("/v1/document2/normalize", {"document": document})
    )


def outline_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    return _require_success_outline(
        _post("/v1/document2/outline", {"document": document})
    )


def reference_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    return _require_success_references(
        _post("/v1/document2/references", {"document": document})
    )


def reference_index_document(document: dict[str, Any]) -> dict[str, Any]:
    return _require_success_reference_index(
        _post("/v1/document2/reference-index", {"document": document})
    )


def export_document(document: dict[str, Any]) -> tuple[str, list[str]]:
    return _require_success_export(
        _post("/v1/document2/export", {"document": document})
    )


def diff_documents(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    return _require_success_diff(
        _post("/v1/document2/diff", {"before": before, "after": after})
    )


def apply_document_command(
    document: dict[str, Any],
    command: dict[str, Any],
) -> dict[str, Any]:
    return _require_success_document(
        _post(
            "/v1/document2/commands",
            {"document": document, "command": command},
        )
    )
