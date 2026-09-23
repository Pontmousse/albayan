from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from mcp.server.auth.provider import AccessToken

_DEVELOPER_ROLE = "developer"


@dataclass(frozen=True)
class _BearerRequest:
    """Minimal request adapter accepted by Clerk authenticate_request()."""

    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class DeveloperRoleTokenVerifier:
    """Authenticate Clerk OAuth and authorize only role=developer users.

    Any authentication failure, Clerk lookup failure, missing metadata, or role
    mismatch returns None so the MCP auth layer rejects the request without
    leaking account details.
    """

    def __init__(self, *, clerk_secret_key: str) -> None:
        self._clerk = Clerk(bearer_auth=clerk_secret_key)

    async def verify_token(self, token: str) -> AccessToken | None:
        cleaned = token.strip()
        if not cleaned:
            return None
        return await asyncio.to_thread(self._verify_sync, cleaned)

    def _verify_sync(self, token: str) -> AccessToken | None:
        try:
            state = self._clerk.authenticate_request(
                _BearerRequest(token),
                AuthenticateRequestOptions(accepts_token=["oauth_token"]),
            )
        except Exception:
            return None

        payload = state.payload if state.is_signed_in else None
        if not isinstance(payload, dict):
            return None

        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.strip():
            return None

        try:
            user = self._clerk.users.get(user_id=user_id)
        except Exception:
            return None

        metadata = getattr(user, "public_metadata", None)
        role = metadata.get("role") if isinstance(metadata, dict) else None
        if role != _DEVELOPER_ROLE:
            return None

        client_id: Any = payload.get("azp")
        if not isinstance(client_id, str) or not client_id.strip():
            client_id = "albayan-dev-mcp"

        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=["openid", "profile", "email", "offline_access"],
        )
