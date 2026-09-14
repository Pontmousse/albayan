"""Best-effort, sanitized analytics for inbound MCP tool calls."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import time
from collections.abc import Awaitable, Callable, Mapping
from itertools import islice
from typing import Any

from opentelemetry.trace import get_current_span
from pydantic import BaseModel

from albayan_mcp.api_client import BackendApiError, api_request

logger = logging.getLogger(__name__)

INPUT_LIMIT_BYTES = 32 * 1024
OUTPUT_LIMIT_BYTES = 64 * 1024
MAX_DEPTH = 12
MAX_CHILDREN = 100
MAX_STRING_LENGTH = 4_096
MAX_ERROR_LENGTH = 2_000
LOGGING_TIMEOUT_SECONDS = 2.0

_REDACTED = "[REDACTED]"
_CREDENTIAL_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "password",
    "secret",
    "download_url",
    "blob",
}
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    return value


def sanitize_snapshot(value: Any, *, max_bytes: int) -> dict[str, Any]:
    """Return a JSON object with bounded depth, breadth, strings, and size."""

    def walk(item: Any, depth: int) -> Any:
        item = _normalize(item)
        if depth > MAX_DEPTH:
            return {"_truncated": "maximum_depth"}
        if item is None or isinstance(item, (bool, int)):
            return item
        if isinstance(item, float):
            return item if math.isfinite(item) else f"<{item}>"
        if isinstance(item, str):
            if len(item) <= MAX_STRING_LENGTH:
                return item
            marker = "…[truncated]"
            return item[: MAX_STRING_LENGTH - len(marker)] + marker
        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            is_image_content = item.get("type") == "image"
            entries = list(islice(item.items(), MAX_CHILDREN + 1))
            kept = entries[: MAX_CHILDREN - 1] if len(entries) > MAX_CHILDREN else entries
            for raw_key, child in kept:
                key = str(raw_key)[:MAX_STRING_LENGTH]
                if key.casefold() in _CREDENTIAL_KEYS or (
                    is_image_content and key.casefold() == "data"
                ):
                    result[key] = _REDACTED
                else:
                    result[key] = walk(child, depth + 1)
            if len(entries) > MAX_CHILDREN:
                result["_truncated_children"] = "at_least_one"
            return result
        if isinstance(item, (list, tuple, set, frozenset)):
            children = list(islice(iter(item), MAX_CHILDREN + 1))
            kept = children[: MAX_CHILDREN - 1] if len(children) > MAX_CHILDREN else children
            result = [walk(child, depth + 1) for child in kept]
            if len(children) > MAX_CHILDREN:
                result.append({"_truncated_children": "at_least_one"})
            return result
        return f"<{type(item).__name__}>"

    sanitized = walk(value, 0)
    if not isinstance(sanitized, dict):
        sanitized = {"value": sanitized}
    encoded = json.dumps(
        sanitized,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) <= max_bytes:
        return sanitized
    return {
        "_mcp_log": {
            "truncated": True,
            "original_size_bytes": len(encoded),
            "limit_bytes": max_bytes,
        }
    }


def _trace_id() -> str | None:
    context = get_current_span().get_span_context()
    if not context.is_valid or not context.trace_id:
        return None
    return f"{context.trace_id:032x}"


def _tool_details(params: Any) -> tuple[str | None, dict[str, Any]]:
    if not isinstance(params, Mapping):
        return None, {}
    name = params.get("name")
    arguments = params.get("arguments")
    return (
        name.strip() if isinstance(name, str) and name.strip() else None,
        dict(arguments) if isinstance(arguments, Mapping) else {},
    )


def _command_name(arguments: Mapping[str, Any]) -> str | None:
    command = arguments.get("command")
    if not isinstance(command, Mapping):
        return None
    operation = command.get("op")
    if not isinstance(operation, str) or not operation.strip():
        return None
    return operation.strip()[:100]


def _is_error_result(result: Any) -> bool:
    result = _normalize(result)
    if isinstance(result, Mapping):
        return result.get("isError") is True or result.get("is_error") is True
    return False


def _safe_error(error: BaseException | None, result: Any = None) -> str:
    if isinstance(error, BackendApiError):
        payload: dict[str, Any] = {
            "status": error.status,
            "code": error.code,
            "message": error.message,
        }
        if error.current_revision is not None:
            payload["current_revision"] = error.current_revision
        if error.issues:
            payload["issues"] = error.issues
        message = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif error is not None:
        message = f"MCP tool call failed ({type(error).__name__})."
    else:
        message = "MCP tool returned an error result."
        normalized = _normalize(result)
        if isinstance(normalized, Mapping):
            content = normalized.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, Mapping):
                        continue
                    text = item.get("text")
                    if not isinstance(text, str):
                        continue
                    try:
                        parsed = json.loads(text)
                    except ValueError:
                        continue
                    if isinstance(parsed, dict):
                        allowed = {
                            key: parsed[key]
                            for key in ("status", "code", "message", "current_revision")
                            if key in parsed
                        }
                        if allowed:
                            message = json.dumps(
                                allowed,
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                            break
    return _BEARER_PATTERN.sub("Bearer [REDACTED]", message)[:MAX_ERROR_LENGTH]


async def _post_log(event: dict[str, Any]) -> None:
    try:
        async with asyncio.timeout(LOGGING_TIMEOUT_SECONDS):
            await api_request(
                "POST",
                "/api/v1/mcp/call-logs",
                json=event,
                timeout=LOGGING_TIMEOUT_SECONDS,
            )
    except Exception as exc:  # analytics must never affect the tool call
        logger.warning("MCP call analytics unavailable (%s).", type(exc).__name__)


class McpCallLoggingMiddleware:
    """Observe every actual protocol `tools/call` at one interception point."""

    async def __call__(
        self,
        ctx: Any,
        call_next: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        if ctx.method != "tools/call":
            return await call_next(ctx)

        tool_name, arguments = _tool_details(ctx.params)
        tool_name = tool_name or "<invalid>"

        started = time.perf_counter_ns()
        trace_id = _trace_id()
        try:
            result = await call_next(ctx)
        except Exception as exc:
            duration_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
            await _post_log(
                {
                    "trace_id": trace_id,
                    "tool_name": tool_name[:100],
                    "command_name": _command_name(arguments),
                    "status": "error",
                    "duration_ms": duration_ms,
                    "input": sanitize_snapshot(arguments, max_bytes=INPUT_LIMIT_BYTES),
                    "output": None,
                    "error": _safe_error(exc),
                }
            )
            raise

        duration_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
        is_error = _is_error_result(result)
        await _post_log(
            {
                "trace_id": trace_id,
                "tool_name": tool_name[:100],
                "command_name": _command_name(arguments),
                "status": "error" if is_error else "success",
                "duration_ms": duration_ms,
                "input": sanitize_snapshot(arguments, max_bytes=INPUT_LIMIT_BYTES),
                "output": (
                    None
                    if is_error
                    else sanitize_snapshot(result, max_bytes=OUTPUT_LIMIT_BYTES)
                ),
                "error": _safe_error(None, result) if is_error else None,
            }
        )
        return result
