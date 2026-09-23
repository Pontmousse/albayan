from __future__ import annotations

from types import SimpleNamespace

from albayan_dev_mcp.auth import DeveloperRoleTokenVerifier


class _FakeUsers:
    def __init__(self, role: str | None) -> None:
        self.role = role

    def get(self, *, user_id: str):
        assert user_id == "user_dev"
        metadata = {} if self.role is None else {"role": self.role}
        return SimpleNamespace(public_metadata=metadata)


class _FakeClerk:
    def __init__(self, role: str | None, *, signed_in: bool = True) -> None:
        self.users = _FakeUsers(role)
        self.signed_in = signed_in

    def authenticate_request(self, request, options):
        assert request.headers["Authorization"] == "Bearer token"
        assert options.accepts_token == ["oauth_token"]
        return SimpleNamespace(
            is_signed_in=self.signed_in,
            payload={"sub": "user_dev", "azp": "chatgpt"} if self.signed_in else None,
        )


def _verifier(role: str | None, *, signed_in: bool = True) -> DeveloperRoleTokenVerifier:
    verifier = object.__new__(DeveloperRoleTokenVerifier)
    verifier._clerk = _FakeClerk(role, signed_in=signed_in)
    return verifier


async def test_developer_role_is_authorized() -> None:
    access = await _verifier("developer").verify_token("token")

    assert access is not None
    assert access.token == "token"
    assert access.client_id == "chatgpt"
    assert "openid" in access.scopes


async def test_non_developer_role_is_rejected() -> None:
    assert await _verifier("author").verify_token("token") is None
    assert await _verifier(None).verify_token("token") is None


async def test_unsigned_or_empty_token_is_rejected() -> None:
    assert await _verifier("developer", signed_in=False).verify_token("token") is None
    assert await _verifier("developer").verify_token("   ") is None
