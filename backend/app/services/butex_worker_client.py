"""Private client for the BuTeX document worker."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_BODY_BYTES = 5 * 1024 * 1024
_TIMEOUT_SECONDS = 15.0
_EXPECTED_WORKER_STATUSES = {400, 401, 404, 413, 422}

_UNCONFIGURED = HTTPException(
    status_code=503,
    detail="عامل BuTeX غير مُهيّأ على الخادم.",
)


def _request_id() -> str:
    # A stable host request ID can be threaded in later; for now avoid leaking payloads.
    return "albayan-backend"


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

    try:
        with httpx.Client(base_url=base, timeout=_TIMEOUT_SECONDS) as client:
            response = client.post(
                path,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Request-ID": _request_id(),
                },
            )
    except httpx.TimeoutException as exc:
        logger.warning("BuTeX worker request timed out: %s", path)
        raise HTTPException(status_code=504, detail="انتهت مهلة عامل BuTeX.") from exc
    except httpx.HTTPError as exc:
        logger.warning("BuTeX worker request failed: %s", path)
        raise HTTPException(status_code=502, detail="تعذّر الاتصال بعامل BuTeX.") from exc

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


def export_document(document: dict[str, Any]) -> tuple[str, list[str]]:
    return _require_success_export(
        _post("/v1/document2/export", {"document": document})
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
