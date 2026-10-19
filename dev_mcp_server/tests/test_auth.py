from __future__ import annotations

import logging
from enum import Enum
from types import SimpleNamespace

from albayan_dev_mcp.auth import DeveloperMetadataTokenVerifier


class _FakeReason(Enum):
    TOKEN_INVALID = "token-invalid"


class _FakeStatus(Enum):
    SIGNED_OUT = "signed-out"


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
        auth_fails: bool = False,
    ) -> None:
        self.users = _FakeUsers(developer, fail=user_lookup_fails)
        self.signed_in = signed_in
        self.auth_fails = auth_fails

    def authenticate_request(self, request, options):
        assert request.headers["Authorization"].startswith("Bearer ")
        assert options.accepts_token == ["oauth_token", "session_token"]
        if self.auth_fails:
            raise RuntimeError("OAuth token invalid: do-not-log-details")
        return SimpleNamespace(
            is_signed_in=self.signed_in,
            payload={"sub": "user_dev", "azp": "chatgpt"} if self.signed_in else None,
            reason=None if self.signed_in else _FakeReason.TOKEN_INVALID,
            status=None if self.signed_in else _FakeStatus.SIGNED_OUT,
        )


def _verifier(
    developer: object = None,
    *,
    signed_in: bool = True,
    user_lookup_fails: bool = False,
    auth_fails: bool = False,
) -> DeveloperMetadataTokenVerifier:
    verifier = object.__new__(DeveloperMetadataTokenVerifier)
    verifier._clerk = _FakeClerk(
        developer,
        signed_in=signed_in,
        user_lookup_fails=user_lookup_fails,
        auth_fails=auth_fails,
    )
    return verifier


async def test_developer_true_is_authorized() -> None:
    access = await _verifier(True).verify_token("token")

    assert access is not None
    assert access.token == "token"
    assert access.client_id == "chatgpt"
    assert "openid" in access.scopes


async def test_chatgpt_session_jwt_shape_is_allowed_through_clerk_verification() -> None:
    token = "header.payload.signature"

    access = await _verifier(True).verify_token(token)

    assert access is not None
    assert access.token == token
    assert access.client_id == "chatgpt"


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


async def test_auth_failure_logs_stage_without_token_or_exception_message(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="albayan_dev_mcp.auth")
    secret_token = "super-secret-bearer-token"

    assert await _verifier(True, auth_fails=True).verify_token(secret_token) is None

    assert "stage=authenticate_request" in caplog.text
    assert "exception_type=RuntimeError" in caplog.text
    assert "token_shape=other" in caplog.text
    assert secret_token not in caplog.text
    assert "do-not-log-details" not in caplog.text


async def test_signed_out_logs_safe_clerk_reason_and_token_shape(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="albayan_dev_mcp.auth")
    secret_token = "oat_super-secret-token"

    assert await _verifier(True, signed_in=False).verify_token(secret_token) is None

    assert "stage=not_signed_in" in caplog.text
    assert "reason=TOKEN_INVALID" in caplog.text
    assert "status=SIGNED_OUT" in caplog.text
    assert "token_shape=oauth_opaque" in caplog.text
    assert secret_token not in caplog.text


async def test_user_lookup_failure_logs_stage_without_account_identifiers(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="albayan_dev_mcp.auth")

    assert (
        await _verifier(True, user_lookup_fails=True).verify_token("token")
        is None
    )

    assert "stage=user_lookup" in caplog.text
    assert "exception_type=RuntimeError" in caplog.text
    assert "user_dev" not in caplog.text


async def test_developer_gate_logs_rejection_shape_without_metadata_value(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="albayan_dev_mcp.auth")

    assert await _verifier("true").verify_token("token") is None

    assert "stage=developer_flag_not_true" in caplog.text
    assert "value_type=str" in caplog.text
    assert 'developer="true"' not in caplog.text
