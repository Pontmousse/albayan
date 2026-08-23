"""تمرير Bearer إلى FastAPI — لا مصادقة هنا."""

from __future__ import annotations

from contextvars import ContextVar

import httpx

from albayan_mcp.settings import settings

_current_bearer: ContextVar[str | None] = ContextVar("current_bearer", default=None)


def set_current_bearer(token: str | None) -> None:
    _current_bearer.set(token)


def get_bearer_token() -> str:
    token = _current_bearer.get()
    if not token:
        token = settings.albayan_agent_token.strip()
    if not token:
        raise RuntimeError(
            "لا يوجد مفتاح مصادقة. عيّن ALBAYAN_AGENT_TOKEN (stdio) "
            "أو أرسل Authorization: Bearer (Streamable HTTP)."
        )
    return token


async def api_get(path: str, token: str | None = None) -> dict:
    bearer = token or get_bearer_token()
    base = settings.albayan_api_url.rstrip("/")
    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        response = await client.get(
            path,
            headers={"Authorization": f"Bearer {bearer}"},
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("استجابة API غير متوقعة.")
        return data
