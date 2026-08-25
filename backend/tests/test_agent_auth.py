"""اختبارات مصادقة الوكلاء."""

from __future__ import annotations

import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.core.actor import Actor, current_actor_user, get_current_actor
from app.core.agent_auth import (
    MCP_OAUTH_SCOPES,
    require_scope,
    resolve_agent_principal,
)
from app.core.agent_auth import AuthPrincipal
from app.core.clerk import AuthContext, get_auth_context
from app.models.agent_token import AgentToken
from app.models.user import User


class RequireScopeTests(unittest.TestCase):
    def test_allows_when_scope_present(self) -> None:
        principal = AuthPrincipal(
            user_id=uuid.uuid4(),
            clerk_id="user_1",
            scopes=frozenset({"profile:read"}),
            auth_method="api_key",
        )
        require_scope(principal, "profile:read")

    def test_rejects_missing_scope(self) -> None:
        principal = AuthPrincipal(
            user_id=uuid.uuid4(),
            clerk_id="user_1",
            scopes=frozenset({"articles:read"}),
            auth_method="api_key",
        )
        with self.assertRaises(HTTPException) as ctx:
            require_scope(principal, "profile:read")
        self.assertEqual(ctx.exception.status_code, 403)


class ResolveAgentPrincipalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = MagicMock()
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            clerk_id="user_test",
            email="test@example.com",
        )

    @patch("app.core.agent_auth.settings")
    def test_rejects_when_mcp_disabled(self, settings_mock: MagicMock) -> None:
        settings_mock.mcp_enabled = False
        self.request.headers.get.return_value = "Bearer alb_abc"
        with self.assertRaises(HTTPException) as ctx:
            resolve_agent_principal(self.request, self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    @patch("app.core.agent_auth.agent_token_service.authenticate_agent_token")
    @patch("app.core.agent_auth.settings")
    def test_resolves_api_key(
        self,
        settings_mock: MagicMock,
        authenticate_mock: MagicMock,
    ) -> None:
        settings_mock.mcp_enabled = True
        self.request.headers.get.return_value = "Bearer alb_secret"
        token_row = AgentToken(
            id=uuid.uuid4(),
            user_id=self.user_id,
            token_hash="hash",
            label="test",
            scopes=["profile:read", "articles:read"],
        )
        authenticate_mock.return_value = (token_row, self.user)

        principal = resolve_agent_principal(self.request, self.db)

        self.assertEqual(principal.user_id, self.user_id)
        self.assertEqual(principal.auth_method, "api_key")
        self.assertIn("profile:read", principal.scopes)
        authenticate_mock.assert_called_once_with(self.db, "alb_secret")

    @patch("app.core.agent_auth.current_user")
    @patch("app.core.agent_auth.get_auth_context")
    @patch("app.core.agent_auth.settings")
    def test_resolves_oauth_jwt(
        self,
        settings_mock: MagicMock,
        get_auth_mock: MagicMock,
        current_user_mock: MagicMock,
    ) -> None:
        settings_mock.mcp_enabled = True
        self.request.headers.get.return_value = "Bearer clerk.jwt.token"
        auth_ctx = MagicMock(clerk_id="user_test")
        get_auth_mock.return_value = auth_ctx
        current_user_mock.return_value = self.user

        principal = resolve_agent_principal(self.request, self.db)

        self.assertEqual(principal.auth_method, "oauth")
        self.assertEqual(principal.scopes, MCP_OAUTH_SCOPES)


class CurrentActorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = MagicMock()
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            clerk_id="user_test",
            email="test@example.com",
        )

    @patch("app.core.actor.current_user")
    @patch("app.core.actor.get_auth_context")
    def test_valid_clerk_user_returns_human_actor(
        self,
        get_auth_mock: MagicMock,
        current_user_mock: MagicMock,
    ) -> None:
        self.request.headers.get.return_value = "Bearer clerk.jwt.token"
        get_auth_mock.return_value = AuthContext(
            clerk_id="user_test",
            email="test@example.com",
            full_name="Test User",
        )
        current_user_mock.return_value = self.user

        actor = get_current_actor(self.request, self.db)

        self.assertEqual(actor.user_id, self.user_id)
        self.assertEqual(actor.clerk_id, "user_test")
        self.assertEqual(actor.auth_method, "human")
        self.assertIsNone(actor.token_id)

    @patch("app.core.actor.agent_token_service.authenticate_agent_token")
    @patch("app.core.actor.settings")
    def test_valid_agent_token_returns_agent_actor(
        self,
        settings_mock: MagicMock,
        authenticate_mock: MagicMock,
    ) -> None:
        settings_mock.mcp_enabled = True
        self.request.headers.get.return_value = "Bearer alb_secret"
        token_id = uuid.uuid4()
        token_row = AgentToken(
            id=token_id,
            user_id=self.user_id,
            token_hash="hash",
            label="test",
            scopes=["profile:read"],
        )
        authenticate_mock.return_value = (token_row, self.user)

        actor = get_current_actor(self.request, self.db)

        self.assertEqual(actor.user_id, self.user_id)
        self.assertEqual(actor.clerk_id, "user_test")
        self.assertEqual(actor.auth_method, "agent")
        self.assertEqual(actor.token_id, token_id)

    @patch("app.core.actor.agent_token_service.authenticate_agent_token")
    @patch("app.core.actor.settings")
    def test_invalid_agent_token_is_rejected(
        self,
        settings_mock: MagicMock,
        authenticate_mock: MagicMock,
    ) -> None:
        settings_mock.mcp_enabled = True
        self.request.headers.get.return_value = "Bearer alb_bad"
        authenticate_mock.side_effect = HTTPException(
            status_code=401,
            detail="مفتاح الوكيل غير صالح.",
        )

        with self.assertRaises(HTTPException) as ctx:
            get_current_actor(self.request, self.db)

        self.assertEqual(ctx.exception.status_code, 401)

    @patch("app.core.actor.settings")
    def test_agent_token_rejected_when_mcp_disabled(
        self,
        settings_mock: MagicMock,
    ) -> None:
        settings_mock.mcp_enabled = False
        self.request.headers.get.return_value = "Bearer alb_secret"

        with self.assertRaises(HTTPException) as ctx:
            get_current_actor(self.request, self.db)

        self.assertEqual(ctx.exception.status_code, 404)

    def test_current_actor_user_returns_resolved_user(self) -> None:
        actor = Actor(
            user_id=self.user_id,
            clerk_id="user_test",
            auth_method="agent",
        )
        self.db.get.return_value = self.user

        user = current_actor_user(actor, self.db)

        self.assertIs(user, self.user)
        self.db.get.assert_called_once_with(User, self.user_id)


class HumanOnlyAuthTests(unittest.TestCase):
    def test_human_only_auth_rejects_agent_token(self) -> None:
        request = MagicMock()
        request.headers.get.return_value = "Bearer alb_secret"

        with self.assertRaises(HTTPException) as ctx:
            get_auth_context(request)

        self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
