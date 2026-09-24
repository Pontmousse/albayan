from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ServiceName = Literal["albayan", "burhan", "butex"]


@dataclass(frozen=True)
class ServiceConfig:
    name: ServiceName
    url: str | None
    token: str | None
    url_env: str
    token_env: str

    @property
    def configured(self) -> bool:
        return bool(self.url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    albayan_dev_url: str | None = None
    burhan_dev_url: str | None = None
    butex_dev_url: str | None = None

    albayan_dev_token: str | None = None
    burhan_dev_token: str | None = None
    butex_dev_token: str | None = None

    # Remote developer MCP authentication. Streamable HTTP is fail-closed unless
    # all three values are configured. Clerk authenticates the caller; the dev
    # MCP additionally requires user.public_metadata.developer is True.
    clerk_issuer_url: str = ""
    clerk_secret_key: str = ""
    dev_mcp_resource_url: str = ""

    dev_mcp_host: str = "127.0.0.1"
    dev_mcp_port: int = 8083
    dev_mcp_request_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    # LLM-backed Burhan tiers can legitimately exceed the generic diagnostic timeout.
    # Keep this separate, explicit and bounded.
    dev_mcp_equation_timeout_seconds: float = Field(default=90.0, gt=0, le=180)
    dev_mcp_max_response_bytes: int = Field(default=262_144, ge=1024, le=2_097_152)
    dev_mcp_trace_max_traces: int = Field(default=200, ge=10, le=10_000)
    dev_mcp_trace_max_events_per_trace: int = Field(default=50, ge=5, le=1_000)

    def service(self, name: ServiceName) -> ServiceConfig:
        mapping: dict[ServiceName, tuple[str | None, str | None, str, str]] = {
            "albayan": (
                self.albayan_dev_url,
                self.albayan_dev_token,
                "ALBAYAN_DEV_URL",
                "ALBAYAN_DEV_TOKEN",
            ),
            "burhan": (
                self.burhan_dev_url,
                self.burhan_dev_token,
                "BURHAN_DEV_URL",
                "BURHAN_DEV_TOKEN",
            ),
            "butex": (
                self.butex_dev_url,
                self.butex_dev_token,
                "BUTEX_DEV_URL",
                "BUTEX_DEV_TOKEN",
            ),
        }
        raw_url, raw_token, url_env, token_env = mapping[name]
        return ServiceConfig(
            name=name,
            url=_normalize_origin(raw_url, env_name=url_env) if raw_url else None,
            token=raw_token.strip() if raw_token and raw_token.strip() else None,
            url_env=url_env,
            token_env=token_env,
        )

    @property
    def remote_auth_configured(self) -> bool:
        return bool(
            self.clerk_issuer_url.strip()
            and self.clerk_secret_key.strip()
            and self.dev_mcp_resource_url.strip()
        )

    def missing_remote_auth_settings(self) -> list[str]:
        return [
            name
            for name, value in (
                ("CLERK_ISSUER_URL", self.clerk_issuer_url),
                ("CLERK_SECRET_KEY", self.clerk_secret_key),
                ("DEV_MCP_RESOURCE_URL", self.dev_mcp_resource_url),
            )
            if not value.strip()
        ]

    def require_remote_auth_configuration(self) -> None:
        missing = self.missing_remote_auth_settings()
        if missing:
            raise RuntimeError(
                "Streamable HTTP developer MCP requires Clerk developer authentication; "
                f"missing: {', '.join(missing)}"
            )


def _normalize_origin(value: str, *, env_name: str) -> str:
    candidate = value.strip()
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{env_name} must be an http(s) service origin")
    if parsed.username or parsed.password:
        raise ValueError(f"{env_name} must not contain embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{env_name} must not contain a query or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError(f"{env_name} must be an origin without a path prefix")
    return candidate.rstrip("/")
