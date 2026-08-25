"""تمرير Bearer إلى FastAPI — لا مصادقة هنا."""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.auth.middleware.auth_context import get_access_token

from albayan_mcp.settings import settings


def get_backend_bearer_token() -> str:
    # MCP forwards the caller credential; FastAPI owns authorization decisions.
    access_token = get_access_token()
    token = access_token.token if access_token else None
    if not token:
        token = settings.albayan_agent_token.strip()
    if not token:
        raise RuntimeError(
            "لا يوجد مفتاح مصادقة. عيّن ALBAYAN_AGENT_TOKEN (stdio) "
            "أو أرسل Authorization: Bearer (Streamable HTTP)."
        )
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
        response.raise_for_status()
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
