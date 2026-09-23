from __future__ import annotations

from types import SimpleNamespace

from albayan_dev_mcp.auth import DeveloperMetadataTokenVerifier


class _FakeUsers:
    def __init__(self, developer: object = None, *, fail: bool = False) -> None:
        self.developer = developer
        self.fail = fail

    def get(self, *, user_id: str):
        assert user_id == "user_dev"
        if self.fail:
            raise RuntimeError("Clerk unavailable")
        metadata = {} if self.developer is None else {"developer": self.developer}
        return SimpleNamespace(public_metadata=metadata)


class _FakeClerk:
    def __init__(
        self,
        developer: object = None,
        *,
        signed_in: bool = True,
        user_lookup_fails: bool = False,
    ) -> None:
        self.users = _FakeUsers(developer, fail=user_lookup_fails)
        self.signed_in = signed_in

    def authenticate_request(self, request, options):
        assert request.headers["Authorization"] == "Bearer token"
        assert options.accepts_token == ["oauth_token"]
        return SimpleNamespace(
            is_signed_in=self.signed_in,
            payload={"sub": "user_dev", "azp": "chatgpt"} if self.signed_in else None,
        )


def _verifier(
    developer: object = None,
    *,
    signed_in: bool = True,
    user_lookup_fails: bool = False,
) -> DeveloperMetadataTokenVerifier:
    verifier = object.__new__(DeveloperMetadataTokenVerifier)
    verifier._clerk = _FakeClerk(
        developer,
        signed_in=signed_in,
        user_lookup_fails=user_lookup_fails,
    )
    return verifier


async def test_developer_true_is_authorized() -> None:
    access = await _verifier(True).verify_token("token")

    assert access is not None
    assert access.token == "token"
    assert access.client_id == "chatgpt"
    assert "openid" in access.scopes


async def test_non_developer_values_are_rejected() -> None:
    assert await _verifier(False).verify_token("token") is None
    assert await _verifier(None).verify_token("token") is None
    assert await _verifier("true").verify_token("token") is None
    assert await _verifier(1).verify_token("token") is None


async def test_unsigned_empty_or_unverifiable_user_is_rejected() -> None:
    assert await _verifier(True, signed_in=False).verify_token("token") is None
    assert await _verifier(True).verify_token("   ") is None
    assert (
        await _verifier(True, user_lookup_fails=True).verify_token("token")
        is None
    )
