from __future__ import annotations

import json
import logging
import re
import uuid
from contextvars import ContextVar
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

TRACE_HEADER = "X-Trace-Id"
_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_current_trace_id: ContextVar[str | None] = ContextVar("albayan_trace_id", default=None)
logger = logging.getLogger("albayan.trace")


def _normalize_or_generate_trace_id(value: str | None) -> str:
    if value:
        candidate = value.strip()
        if _TRACE_ID_PATTERN.fullmatch(candidate):
            return candidate
    return str(uuid.uuid4())


def current_trace_id() -> str | None:
    return _current_trace_id.get()


def trace_headers() -> dict[str, str]:
    trace_id = current_trace_id()
    return {TRACE_HEADER: trace_id} if trace_id else {}


def emit_trace_event(
    *,
    service: str,
    stage: str,
    status: str,
    duration_ms: float | None = None,
    **details: Any,
) -> None:
    trace_id = current_trace_id()
    if not trace_id:
        return
    payload: dict[str, Any] = {
        "trace_id": trace_id,
        "service": service,
        "stage": stage,
        "status": status,
    }
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 3)
    if details:
        payload["details"] = details
    logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Attach a safe correlation ID to every backend request.

    The ID is observability metadata only. It never participates in authentication
    or authorization. Full request/response bodies are intentionally not logged.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(TRACE_HEADER)
        trace_id = _normalize_or_generate_trace_id(incoming)
        token = _current_trace_id.set(trace_id)
        started = perf_counter()
        emit_trace_event(
            service="albayan-backend",
            stage="request",
            status="started",
            method=request.method,
            path=request.url.path,
            incoming_trace_accepted=bool(incoming and incoming.strip() == trace_id),
        )
        try:
            response = await call_next(request)
        except Exception:
            emit_trace_event(
                service="albayan-backend",
                stage="request",
                status="error",
                duration_ms=(perf_counter() - started) * 1000,
                method=request.method,
                path=request.url.path,
            )
            raise
        else:
            response.headers[TRACE_HEADER] = trace_id
            emit_trace_event(
                service="albayan-backend",
                stage="request",
                status="ok" if response.status_code < 500 else "error",
                duration_ms=(perf_counter() - started) * 1000,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )
            return response
        finally:
            _current_trace_id.reset(token)
