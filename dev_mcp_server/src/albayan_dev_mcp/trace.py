from __future__ import annotations

import re
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Protocol

TRACE_HEADER = "X-Trace-Id"
_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def new_trace_id() -> str:
    return str(uuid.uuid4())


def validate_trace_id(value: str) -> str:
    candidate = value.strip()
    if not _TRACE_ID_PATTERN.fullmatch(candidate):
        raise ValueError(
            "trace_id must be 1-128 characters using letters, digits, '.', '_', ':', or '-'"
        )
    return candidate


def resolve_trace_id(value: str | None) -> str:
    if value is None or not value.strip():
        return new_trace_id()
    return validate_trace_id(value)


@dataclass(frozen=True)
class TraceEvent:
    trace_id: str
    sequence: int
    timestamp: str
    service: str
    stage: str
    status: str
    duration_ms: float | None = None
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "service": self.service,
            "stage": self.stage,
            "status": self.status,
        }
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.details:
            payload["details"] = self.details
        return payload


class TraceSource(Protocol):
    name: str
    persistent: bool
    coverage: tuple[str, ...]

    def record(
        self,
        *,
        trace_id: str,
        service: str,
        stage: str,
        status: str,
        duration_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> TraceEvent: ...

    def get_trace(self, trace_id: str) -> list[TraceEvent]: ...

    def list_recent(self, *, limit: int) -> list[dict[str, Any]]: ...


class InMemoryTraceSource:
    """Small bounded trace source for one dev-MCP process.

    This intentionally does not pretend to be centralized tracing. It provides a
    safe Phase-2 source abstraction and preserves dev-MCP request/correlation
    evidence until a Railway/OpenTelemetry/etc. adapter is configured later.
    """

    name = "in_memory"
    persistent = False
    coverage = ("dev_mcp",)

    def __init__(self, *, max_traces: int = 200, max_events_per_trace: int = 50):
        self.max_traces = max_traces
        self.max_events_per_trace = max_events_per_trace
        self._events: OrderedDict[str, list[TraceEvent]] = OrderedDict()
        self._next_sequence: dict[str, int] = {}
        self._lock = RLock()

    def record(
        self,
        *,
        trace_id: str,
        service: str,
        stage: str,
        status: str,
        duration_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> TraceEvent:
        trace_id = validate_trace_id(trace_id)
        with self._lock:
            sequence = self._next_sequence.get(trace_id, 0) + 1
            self._next_sequence[trace_id] = sequence
            event = TraceEvent(
                trace_id=trace_id,
                sequence=sequence,
                timestamp=datetime.now(UTC).isoformat(),
                service=service,
                stage=stage,
                status=status,
                duration_ms=round(duration_ms, 3) if duration_ms is not None else None,
                details=details or None,
            )
            events = self._events.setdefault(trace_id, [])
            events.append(event)
            if len(events) > self.max_events_per_trace:
                del events[: len(events) - self.max_events_per_trace]
            self._events.move_to_end(trace_id)
            while len(self._events) > self.max_traces:
                removed_trace_id, _ = self._events.popitem(last=False)
                self._next_sequence.pop(removed_trace_id, None)
            return event

    def get_trace(self, trace_id: str) -> list[TraceEvent]:
        trace_id = validate_trace_id(trace_id)
        with self._lock:
            return list(self._events.get(trace_id, ()))

    def list_recent(self, *, limit: int) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, self.max_traces))
        with self._lock:
            summaries: list[dict[str, Any]] = []
            for trace_id, events in reversed(self._events.items()):
                if not events:
                    continue
                summaries.append(
                    {
                        "trace_id": trace_id,
                        "event_count": len(events),
                        "first_timestamp": events[0].timestamp,
                        "last_timestamp": events[-1].timestamp,
                        "last_service": events[-1].service,
                        "last_stage": events[-1].stage,
                        "last_status": events[-1].status,
                    }
                )
                if len(summaries) >= bounded_limit:
                    break
            return summaries
