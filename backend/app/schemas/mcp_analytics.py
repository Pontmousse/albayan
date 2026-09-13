from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.mcp_log_sanitization import sanitize_error, sanitize_snapshot

McpCallStatus = Literal["success", "error"]
McpAnalyticsPeriod = Literal["24h", "7d", "30d", "90d"]

MCP_INPUT_SNAPSHOT_MAX_BYTES = 32 * 1024
MCP_OUTPUT_SNAPSHOT_MAX_BYTES = 64 * 1024


def _json_size(value: dict[str, Any]) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )


class McpCallLogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    trace_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    tool_name: str = Field(min_length=1, max_length=100)
    command_name: str | None = Field(default=None, min_length=1, max_length=100)
    status: McpCallStatus
    duration_ms: int = Field(ge=0)
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=2000)

    @field_validator("input", mode="before")
    @classmethod
    def _sanitize_input(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("input must be a JSON object")
        return sanitize_snapshot(value, max_bytes=MCP_INPUT_SNAPSHOT_MAX_BYTES)

    @field_validator("output", mode="before")
    @classmethod
    def _sanitize_output(cls, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("output must be a JSON object")
        return sanitize_snapshot(value, max_bytes=MCP_OUTPUT_SNAPSHOT_MAX_BYTES)

    @field_validator("tool_name", "command_name", mode="before")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @field_validator("error", mode="before")
    @classmethod
    def _sanitize_error(cls, value: str | None) -> str | None:
        return sanitize_error(value)

    @model_validator(mode="after")
    def _validate_result_and_snapshot_sizes(self):
        if _json_size(self.input) > MCP_INPUT_SNAPSHOT_MAX_BYTES:
            raise ValueError("input snapshot exceeds the 32 KiB limit")
        if self.output is not None and _json_size(self.output) > MCP_OUTPUT_SNAPSHOT_MAX_BYTES:
            raise ValueError("output snapshot exceeds the 64 KiB limit")
        if self.status == "success":
            if self.output is None or self.error is not None:
                raise ValueError("successful calls require output and cannot include error")
        elif not self.error or self.output is not None:
            raise ValueError("failed calls require error and cannot include output")
        return self


class McpAnalyticsSummary(BaseModel):
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    average_duration_ms: int
    commands_run: int
    unique_users: int
    previous_period_change_percent: float | None = None


class McpTimeBucket(BaseModel):
    started_at: datetime
    total_calls: int
    successful_calls: int
    failed_calls: int


class McpToolUsage(BaseModel):
    tool_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    average_duration_ms: int
    share_percent: float


class McpCommandUsage(BaseModel):
    command_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    share_percent: float


class McpCommandGroupUsage(BaseModel):
    key: str
    total_calls: int
    commands: list[McpCommandUsage]


class McpAnalyticsRead(BaseModel):
    period: McpAnalyticsPeriod
    starts_at: datetime
    ends_at: datetime
    bucket_granularity: Literal["hour", "day"]
    summary: McpAnalyticsSummary
    timeline: list[McpTimeBucket]
    tools: list[McpToolUsage]
    command_groups: list[McpCommandGroupUsage]


class McpCallActorRead(BaseModel):
    id: UUID
    email: str
    full_name: str | None


class McpCallListItem(BaseModel):
    id: UUID
    created_at: datetime
    actor: McpCallActorRead | None
    trace_id: str | None
    tool_name: str
    command_name: str | None
    status: McpCallStatus
    duration_ms: int


class McpCallListRead(BaseModel):
    items: list[McpCallListItem]
    next_cursor: str | None


class McpCallDetailRead(McpCallListItem):
    input: dict[str, Any]
    output: dict[str, Any] | None
    error: str | None
