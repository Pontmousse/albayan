"""تمرير Bearer إلى FastAPI — لا مصادقة هنا."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.exceptions import ToolError

from albayan_mcp.settings import settings

logger = logging.getLogger(__name__)


class BackendApiError(ToolError):
    """Safe, machine-readable FastAPI failure surfaced as an MCP tool error."""

    def __init__(
        self,
        *,
        status: int,
        code: str,
        message: str,
        current_revision: int | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.current_revision = current_revision
        payload: dict[str, Any] = {
            "status": status,
            "code": code,
            "message": message,
        }
        if current_revision is not None:
            payload["current_revision"] = current_revision
        super().__init__(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def _backend_error(response: httpx.Response) -> BackendApiError:
    default_messages = {
        401: "تعذرت المصادقة لدى الخادم الخلفي.",
        403: "ليست لديك صلاحية لتنفيذ هذه العملية.",
        404: "تعذر العثور على المورد المطلوب.",
        409: "تعذر تنفيذ العملية بسبب تعارض في الحالة الحالية.",
        422: "رفض الخادم الخلفي بيانات الطلب.",
    }
    code = "backend_error"
    message = default_messages.get(
        response.status_code,
        "تعذر إكمال الطلب لدى الخادم الخلفي.",
    )
    current_revision: int | None = None

    try:
        body = response.json()
    except ValueError:
        body = None
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, dict):
        if isinstance(detail.get("code"), str) and detail["code"].strip():
            code = detail["code"].strip()
        if isinstance(detail.get("message"), str) and detail["message"].strip():
            message = detail["message"].strip()
        value = detail.get("current_revision")
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            current_revision = value
    elif isinstance(detail, list):
        issues: list[str] = []
        for item in detail[:5]:
            if not isinstance(item, dict):
                continue
            location_parts = item.get("loc")
            if isinstance(location_parts, list):
                location = ".".join(
                    str(part)
                    for part in location_parts
                    if isinstance(part, (str, int)) and not isinstance(part, bool)
                )
            else:
                location = ""
            issue_message = item.get("msg")
            if not isinstance(issue_message, str) or not issue_message.strip():
                continue
            summary = issue_message.strip()[:160]
            issues.append(f"{location}: {summary}" if location else summary)
        code = "validation_error"
        if issues:
            message = "بيانات الطلب غير صالحة: " + "; ".join(issues)
    elif isinstance(detail, str) and detail.strip():
        message = detail.strip()

    return BackendApiError(
        status=response.status_code,
        code=code,
        message=message,
        current_revision=current_revision,
    )


def _safe_jwt_claims(token: str) -> dict[str, Any] | None:
    """قراءة iss/aud/exp من JWT بلا تحقق — للتشخيص فقط؛ لا يُسجَّل التوكن."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        raw = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(raw))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return {
        "iss": payload.get("iss"),
        "aud": payload.get("aud"),
        "exp": payload.get("exp"),
        "azp": payload.get("azp"),
    }


def get_backend_bearer_token() -> str:
    # MCP forwards the caller credential; FastAPI owns authorization decisions.
    access_token = get_access_token()
    mcp_token = access_token.token.strip() if access_token and access_token.token else ""
    has_mcp_authorization = bool(mcp_token)
    logger.info("MCP has Authorization: %s", has_mcp_authorization)

    token = mcp_token
    token_source = "mcp"
    if not token:
        token = settings.albayan_agent_token.strip()
        token_source = "albayan_agent_token"
    if not token:
        logger.info("Forwarding Authorization: False")
        raise RuntimeError(
            "لا يوجد مفتاح مصادقة. عيّن ALBAYAN_AGENT_TOKEN (stdio) "
            "أو أرسل Authorization: Bearer (Streamable HTTP)."
        )

    logger.info(
        "Forwarding Authorization: True (source=%s, jwt=%s)",
        token_source,
        bool(_safe_jwt_claims(token)),
    )
    claims = _safe_jwt_claims(token)
    if claims is not None:
        logger.info(
            "Forwarded token claims: iss=%r aud=%r exp=%r azp=%r",
            claims.get("iss"),
            claims.get("aud"),
            claims.get("exp"),
            claims.get("azp"),
        )
    elif token.startswith("alb_"):
        logger.info("Forwarded token kind: alb_ agent key (not a JWT)")
    else:
        logger.info("Forwarded token kind: opaque/non-JWT")

    return token


async def api_request(
    method: str,
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    bearer = get_backend_bearer_token()
    base = settings.albayan_api_url.rstrip("/")
    request_headers = dict(headers or {})
    request_headers["Authorization"] = f"Bearer {bearer}"

    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        response = await client.request(
            method,
            path,
            json=json,
            params=params,
            headers=request_headers,
        )
        if response.status_code >= 400:
            error = _backend_error(response)
            logger.warning(
                "Backend request failed: %s %s -> status=%s code=%s",
                method,
                path,
                error.status,
                error.code,
            )
            raise error
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError("استجابة API ليست JSON صالحة.") from exc


def _expect_object(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RuntimeError("استجابة API غير متوقعة: كان المتوقع كائناً.")
    return data


def _expect_list(data: Any) -> list[Any]:
    if not isinstance(data, list):
        raise RuntimeError("استجابة API غير متوقعة: كان المتوقع قائمة.")
    return data


async def api_get_object(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _expect_object(await api_request("GET", path, params=params, headers=headers))


async def api_get_list(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> list[Any]:
    return _expect_list(await api_request("GET", path, params=params, headers=headers))


async def api_post_object(
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _expect_object(
        await api_request("POST", path, json=json, params=params, headers=headers)
    )


async def api_post_list(
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> list[Any]:
    return _expect_list(
        await api_request("POST", path, json=json, params=params, headers=headers)
    )


async def api_patch_object(
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _expect_object(
        await api_request("PATCH", path, json=json, params=params, headers=headers)
    )


async def api_put_object(
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _expect_object(
        await api_request("PUT", path, json=json, params=params, headers=headers)
    )


async def api_delete(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    return await api_request("DELETE", path, params=params, headers=headers)
