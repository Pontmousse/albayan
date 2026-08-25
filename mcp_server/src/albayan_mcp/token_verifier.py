"""تحقق شكلي من وجود Bearer — المصادقة الحقيقية في FastAPI."""

from __future__ import annotations

from mcp.server.auth.provider import AccessToken


class PassThroughTokenVerifier:
    """يقبل أي Bearer ويمرّره إلى FastAPI دون التحقق منه محلياً."""

    async def verify_token(self, token: str) -> AccessToken | None:
        cleaned = token.strip()
        if not cleaned:
            return None
        return AccessToken(
            token=cleaned,
            client_id="mcp-client",
            scopes=["profile:read", "articles:read"],
        )
