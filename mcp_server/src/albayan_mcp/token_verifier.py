"""تحقق شكلي من وجود Bearer — المصادقة الحقيقية في FastAPI."""

from __future__ import annotations

from mcp.server.auth.provider import AccessToken


class PassThroughTokenVerifier:
    """يقبل أي Bearer ويمرّره إلى FastAPI دون التحقق منه محلياً."""

    async def verify_token(self, token: str) -> AccessToken | None:
        cleaned = token.strip()
        if not cleaned:
            return None
        # نطاقات هوية Clerk القياسية (superset يغطي required_scopes)؛
        # صلاحيات التطبيق الفعلية تُفرض في FastAPI لا هنا.
        return AccessToken(
            token=cleaned,
            client_id="mcp-client",
            scopes=["openid", "profile", "email", "offline_access"],
        )
