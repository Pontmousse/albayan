from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Literal, Mapping
from urllib.parse import urlsplit

import httpx

from albayan_dev_mcp.sanitize import sanitize
from albayan_dev_mcp.settings import ServiceName, Settings
from albayan_dev_mcp.trace import TRACE_HEADER, TraceSource, resolve_trace_id

AllowedMethod = Literal["GET", "HEAD", "OPTIONS"]
_SAFE_RESPONSE_HEADERS = {
    "content-length",
    "content-type",
    "server",
    "x-request-id",
    "x-trace-id",
}


class DevHttpClient:
    """Constrained client for explicitly configured development service origins."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        trace_source: TraceSource | None = None,
    ):
        self.settings = settings
        self.transport = transport
        self.trace_source = trace_source

    def _record(
        self,
        *,
        trace_id: str,
        service: str,
        stage: str,
        status: str,
        duration_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if self.trace_source is None:
            return
        self.trace_source.record(
            trace_id=trace_id,
            service=service,
            stage=stage,
            status=status,
            duration_ms=duration_ms,
            details=details,
        )

    async def request(
        self,
        *,
        service: ServiceName,
        method: AllowedMethod,
        path: str,
        query: Mapping[str, str | int | float | bool] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_trace_id = resolve_trace_id(trace_id)
        started = perf_counter()
        self._record(
            trace_id=resolved_trace_id,
            service="dev_mcp",
            stage="http_request",
            status="started",
            details={"target_service": service, "method": method, "path": path},
        )

        config = self.settings.service(service)
        if not config.configured:
            result = _missing_service(config.url_env, service)
            result["trace_id"] = resolved_trace_id
            self._record(
                trace_id=resolved_trace_id,
                service="dev_mcp",
                stage="http_request",
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={"target_service": service, "reason": "missing_configuration"},
            )
            return result

        safe_path = _validate_relative_path(path)
        url = f"{config.url}{safe_path}"
        headers = {
            "Accept": "application/json, text/plain;q=0.9, */*;q=0.1",
            TRACE_HEADER: resolved_trace_id,
        }
        if config.token:
            headers["Authorization"] = f"Bearer {config.token}"

        timeout = self.settings.dev_mcp_request_timeout_seconds
        max_bytes = self.settings.dev_mcp_max_response_bytes

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                async with client.stream(
                    method,
                    url,
                    params=dict(query or {}),
                    headers=headers,
                ) as response:
                    raw, truncated = await _read_bounded(response, max_bytes=max_bytes)
                    safe_headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower() in _SAFE_RESPONSE_HEADERS
                    }
                    body, body_kind = _decode_body(raw, response.headers.get("content-type", ""))
                    downstream_trace_id = response.headers.get(TRACE_HEADER)
                    correlation_preserved = (
                        downstream_trace_id == resolved_trace_id
                        if downstream_trace_id is not None
                        else None
                    )
                    duration_ms = (perf_counter() - started) * 1000
                    self._record(
                        trace_id=resolved_trace_id,
                        service=service,
                        stage="http_response",
                        status="ok" if 200 <= response.status_code < 400 else "error",
                        duration_ms=duration_ms,
                        details={
                            "method": method,
                            "path": safe_path,
                            "status_code": response.status_code,
                            "correlation_preserved": correlation_preserved,
                            "truncated": truncated,
                        },
                    )
                    return {
                        "ok": 200 <= response.status_code < 400,
                        "blocked": False,
                        "trace_id": resolved_trace_id,
                        "correlation_preserved": correlation_preserved,
                        "service": service,
                        "method": method,
                        "path": safe_path,
                        "status_code": response.status_code,
                        "headers": sanitize(safe_headers),
                        "body_kind": body_kind,
                        "body": sanitize(body),
                        "truncated": truncated,
                        "redirect_location_exposed": False,
                    }
        except httpx.TimeoutException:
            self._record(
                trace_id=resolved_trace_id,
                service=service,
                stage="http_response",
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={"reason": "timeout", "method": method, "path": safe_path},
            )
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "service": service,
                "reason": "timeout",
                "human_action": (
                    f"Check that the {service} development service is reachable, or adjust "
                    "DEV_MCP_REQUEST_TIMEOUT_SECONDS if the endpoint is expected to be slow."
                ),
            }
        except httpx.RequestError as exc:
            self._record(
                trace_id=resolved_trace_id,
                service=service,
                stage="http_response",
                status="blocked",
                duration_ms=(perf_counter() - started) * 1000,
                details={
                    "reason": "service_unreachable",
                    "error_type": type(exc).__name__,
                    "method": method,
                    "path": safe_path,
                },
            )
            return {
                "ok": False,
                "blocked": True,
                "trace_id": resolved_trace_id,
                "service": service,
                "reason": "service_unreachable",
                "error_type": type(exc).__name__,
                "human_action": (
                    f"Check the configured {config.url_env} development service and its network access."
                ),
            }

    async def probe(self, service: ServiceName) -> dict[str, Any]:
        config = self.settings.service(service)
        if not config.configured:
            return {
                "configured": False,
                "reachable": None,
                "blocked": True,
                "reason": "missing_configuration",
                "missing": [config.url_env],
                "human_action": f"Configure {config.url_env} for the development MCP connector.",
            }
        result = await self.request(service=service, method="GET", path="/")
        if result.get("reason") in {"timeout", "service_unreachable"}:
            return {
                "configured": True,
                "reachable": False,
                "blocked": True,
                "reason": result["reason"],
                "human_action": result.get("human_action"),
            }
        return {
            "configured": True,
            "reachable": True,
            "blocked": False,
            "status_code": result.get("status_code"),
            "trace_id": result.get("trace_id"),
            "note": "Any HTTP response counts as reachable; the root endpoint may legitimately return an error status.",
        }


def _missing_service(env_name: str, service: ServiceName) -> dict[str, Any]:
    return {
        "ok": False,
        "blocked": True,
        "service": service,
        "reason": "missing_configuration",
        "missing": [env_name],
        "human_action": f"Configure {env_name} for the development MCP connector.",
    }


def _validate_relative_path(path: str) -> str:
    candidate = path.strip()
    if not candidate.startswith("/"):
        raise ValueError("path must start with '/'")
    if candidate.startswith("//") or "\\" in candidate:
        raise ValueError("path must be relative to the configured service origin")
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        raise ValueError("arbitrary URLs are not allowed")
    if parsed.fragment:
        raise ValueError("fragments are not allowed; use query parameters explicitly")
    if parsed.query:
        raise ValueError("put query parameters in the query argument")
    return parsed.path or "/"


async def _read_bounded(response: httpx.Response, *, max_bytes: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    total = 0
    truncated = False
    async for chunk in response.aiter_bytes():
        if total + len(chunk) > max_bytes:
            remaining = max_bytes - total
            if remaining > 0:
                chunks.append(chunk[:remaining])
            truncated = True
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks), truncated


def _decode_body(raw: bytes, content_type: str) -> tuple[Any, str]:
    lowered = content_type.lower()
    text = raw.decode("utf-8", errors="replace")
    if "json" in lowered:
        try:
            return json.loads(text), "json"
        except json.JSONDecodeError:
            return text, "text"
    if lowered.startswith("text/") or not lowered:
        return text, "text"
    return {"bytes": len(raw), "content_type": content_type or None}, "binary_metadata"
