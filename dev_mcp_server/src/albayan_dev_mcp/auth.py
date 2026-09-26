from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from mcp.server.auth.provider import AccessToken


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _BearerRequest:
    """Minimal request adapter accepted by Clerk authenticate_request()."""

    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def _safe_enum_name(value: object) -> str:
    """Return a non-sensitive enum/type label suitable for diagnostics."""

    name = getattr(value, "name", None)
    if isinstance(name, str) and name:
        return name
    if value is None:
        return "none"
    return type(value).__name__


def _token_shape(token: str) -> str:
    """Classify token format without logging any token material."""

    if token.startswith("oat_"):
        return "oauth_opaque"
    if token.count(".") == 2:
        return "jwt_like"
    return "other"


class DeveloperMetadataTokenVerifier:
    """Authenticate Clerk OAuth and authorize only developer=true users.

    Any authentication failure, Clerk lookup failure, missing metadata, or a
    value other than the boolean True returns None so the MCP auth layer rejects
    the request without leaking account details.

    Rejections are logged with coarse stage/reason/type labels only. Bearer
    tokens, Clerk user IDs, emails, metadata values, and raw exception messages
    are deliberately never written to logs.
    """

    def __init__(self, *, clerk_secret_key: str) -> None:
        self._clerk = Clerk(bearer_auth=clerk_secret_key)

    async def verify_token(self, token: str) -> AccessToken | None:
        cleaned = token.strip()
        if not cleaned:
            logger.warning("dev_mcp_auth rejected stage=empty_token")
            return None
        return await asyncio.to_thread(self._verify_sync, cleaned)

    def _verify_sync(self, token: str) -> AccessToken | None:
        try:
            state = self._clerk.authenticate_request(
                _BearerRequest(token),
                AuthenticateRequestOptions(accepts_token=["oauth_token"]),
            )
        except Exception as exc:
            logger.warning(
                "dev_mcp_auth rejected stage=authenticate_request exception_type=%s token_shape=%s",
                type(exc).__name__,
                _token_shape(token),
            )
            return None

        if not state.is_signed_in:
            logger.warning(
                "dev_mcp_auth rejected stage=not_signed_in reason=%s status=%s token_shape=%s",
                _safe_enum_name(getattr(state, "reason", None)),
                _safe_enum_name(getattr(state, "status", None)),
                _token_shape(token),
            )
            return None

        payload = state.payload
        if not isinstance(payload, dict):
            logger.warning(
                "dev_mcp_auth rejected stage=invalid_payload payload_type=%s",
                type(payload).__name__,
            )
            return None

        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.strip():
            logger.warning("dev_mcp_auth rejected stage=missing_subject")
            return None

        try:
            user = self._clerk.users.get(user_id=user_id)
        except Exception as exc:
            logger.warning(
                "dev_mcp_auth rejected stage=user_lookup exception_type=%s",
                type(exc).__name__,
            )
            return None

        metadata = getattr(user, "public_metadata", None)
        if not isinstance(metadata, dict):
            logger.warning(
                "dev_mcp_auth rejected stage=invalid_public_metadata metadata_type=%s",
                type(metadata).__name__,
            )
            return None

        if "developer" not in metadata:
            logger.warning("dev_mcp_auth rejected stage=missing_developer_flag")
            return None

        developer = metadata["developer"]
        if developer is not True:
            logger.warning(
                "dev_mcp_auth rejected stage=developer_flag_not_true value_type=%s",
                type(developer).__name__,
            )
            return None

        client_id: Any = payload.get("azp")
        if not isinstance(client_id, str) or not client_id.strip():
            client_id = "albayan-dev-mcp"

        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=["openid", "profile", "email", "offline_access"],
        )
