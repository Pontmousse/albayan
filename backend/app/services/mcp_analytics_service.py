"""Persistence, aggregation, and retention for MCP tool-call analytics."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.document2_registry import DOCUMENT2_COMMAND_GROUPS
from app.models.mcp_call_log import McpCallLog
from app.models.user import User
from app.schemas.mcp_analytics import (
    McpAnalyticsPeriod,
    McpAnalyticsRead,
    McpAnalyticsSummary,
    McpCallActorRead,
    McpCallDetailRead,
    McpCallListItem,
    McpCallListRead,
    McpCallLogCreate,
    McpCommandGroupUsage,
    McpCommandUsage,
    McpTimeBucket,
    McpToolUsage,
)

MCP_LOG_RETENTION_DAYS = 90
_PERIOD_DELTAS = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}


def create_call_log(
    db: Session,
    *,
    user_id: uuid.UUID,
    payload: McpCallLogCreate,
) -> McpCallLog:
    row = McpCallLog(
        user_id=user_id,
        trace_id=payload.trace_id,
        tool_name=payload.tool_name,
        command_name=payload.command_name,
        status=payload.status,
        duration_ms=payload.duration_ms,
        input_json=payload.input,
        output_json=payload.output,
        error=payload.error,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _period_bounds(
    period: McpAnalyticsPeriod,
    *,
    now: datetime,
) -> tuple[datetime, datetime]:
    return now - _PERIOD_DELTAS[period], now


def _rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def _as_int(value: Any) -> int:
    return int(value or 0)


def _floor_bucket(value: datetime, granularity: str) -> datetime:
    value = value.astimezone(UTC)
    if granularity == "hour":
        return value.replace(minute=0, second=0, microsecond=0)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _timeline(
    rows: list[Any],
    *,
    starts_at: datetime,
    ends_at: datetime,
    granularity: str,
) -> list[McpTimeBucket]:
    observed: dict[datetime, tuple[int, int]] = {}
    for bucket, total, successful in rows:
        if bucket.tzinfo is None:
            bucket = bucket.replace(tzinfo=UTC)
        observed[bucket.astimezone(UTC)] = (_as_int(total), _as_int(successful))

    cursor = _floor_bucket(starts_at, granularity)
    final = _floor_bucket(ends_at, granularity)
    step = timedelta(hours=1) if granularity == "hour" else timedelta(days=1)
    buckets: list[McpTimeBucket] = []
    while cursor <= final:
        total, successful = observed.get(cursor, (0, 0))
        buckets.append(
            McpTimeBucket(
                started_at=cursor,
                total_calls=total,
                successful_calls=successful,
                failed_calls=total - successful,
            )
        )
        cursor += step
    return buckets


def analytics(
    db: Session,
    period: McpAnalyticsPeriod,
    *,
    now: datetime | None = None,
) -> McpAnalyticsRead:
    ends_at = now or datetime.now(UTC)
    starts_at, ends_at = _period_bounds(period, now=ends_at)
    current_filter = and_(
        McpCallLog.created_at >= starts_at,
        McpCallLog.created_at <= ends_at,
    )
    successful = case((McpCallLog.status == "success", 1), else_=0)

    summary_row = db.execute(
        select(
            func.count(McpCallLog.id),
            func.sum(successful),
            func.avg(McpCallLog.duration_ms),
            func.count(McpCallLog.command_name),
            func.count(func.distinct(McpCallLog.user_id)),
        ).where(current_filter)
    ).one()
    total = _as_int(summary_row[0])
    successful_total = _as_int(summary_row[1])
    average_duration = round(float(summary_row[2] or 0))
    commands_run = _as_int(summary_row[3])
    unique_users = _as_int(summary_row[4])

    previous_change: float | None = None
    if period != "90d":
        delta = _PERIOD_DELTAS[period]
        previous_total = _as_int(
            db.scalar(
                select(func.count(McpCallLog.id)).where(
                    McpCallLog.created_at >= starts_at - delta,
                    McpCallLog.created_at < starts_at,
                )
            )
        )
        if previous_total:
            previous_change = round(
                ((total - previous_total) / previous_total) * 100,
                1,
            )

    tool_rows = db.execute(
        select(
            McpCallLog.tool_name,
            func.count(McpCallLog.id),
            func.sum(successful),
            func.avg(McpCallLog.duration_ms),
        )
        .where(current_filter)
        .group_by(McpCallLog.tool_name)
        .order_by(func.count(McpCallLog.id).desc(), McpCallLog.tool_name)
    ).all()
    tools = [
        McpToolUsage(
            tool_name=tool_name,
            total_calls=_as_int(tool_total),
            successful_calls=_as_int(tool_successful),
            failed_calls=_as_int(tool_total) - _as_int(tool_successful),
            average_duration_ms=round(float(tool_average or 0)),
            share_percent=_rate(_as_int(tool_total), total),
        )
        for tool_name, tool_total, tool_successful, tool_average in tool_rows
    ]

    command_rows = db.execute(
        select(
            McpCallLog.command_name,
            func.count(McpCallLog.id),
            func.sum(successful),
        )
        .where(current_filter, McpCallLog.command_name.is_not(None))
        .group_by(McpCallLog.command_name)
    ).all()
    command_counts = {
        command_name: (_as_int(command_total), _as_int(command_successful))
        for command_name, command_total, command_successful in command_rows
        if command_name
    }
    known_commands: set[str] = set()
    command_groups: list[McpCommandGroupUsage] = []
    for group_key, group_commands in DOCUMENT2_COMMAND_GROUPS:
        known_commands.update(group_commands)
        commands = []
        for command_name in group_commands:
            command_total, command_successful = command_counts.get(
                command_name, (0, 0)
            )
            commands.append(
                McpCommandUsage(
                    command_name=command_name,
                    total_calls=command_total,
                    successful_calls=command_successful,
                    failed_calls=command_total - command_successful,
                    share_percent=_rate(command_total, commands_run),
                )
            )
        commands.sort(key=lambda item: (-item.total_calls, item.command_name))
        command_groups.append(
            McpCommandGroupUsage(
                key=group_key,
                total_calls=sum(item.total_calls for item in commands),
                commands=commands,
            )
        )

    unknown_commands = [
        McpCommandUsage(
            command_name=command_name,
            total_calls=command_total,
            successful_calls=command_successful,
            failed_calls=command_total - command_successful,
            share_percent=_rate(command_total, commands_run),
        )
        for command_name, (command_total, command_successful) in command_counts.items()
        if command_name not in known_commands
    ]
    if unknown_commands:
        unknown_commands.sort(key=lambda item: (-item.total_calls, item.command_name))
        command_groups.append(
            McpCommandGroupUsage(
                key="other",
                total_calls=sum(item.total_calls for item in unknown_commands),
                commands=unknown_commands,
            )
        )

    granularity = "hour" if period == "24h" else "day"
    bucket = func.date_trunc(granularity, McpCallLog.created_at)
    timeline_rows = db.execute(
        select(bucket, func.count(McpCallLog.id), func.sum(successful))
        .where(current_filter)
        .group_by(bucket)
        .order_by(bucket)
    ).all()

    return McpAnalyticsRead(
        period=period,
        starts_at=starts_at,
        ends_at=ends_at,
        bucket_granularity=granularity,
        summary=McpAnalyticsSummary(
            total_calls=total,
            successful_calls=successful_total,
            failed_calls=total - successful_total,
            success_rate=_rate(successful_total, total),
            average_duration_ms=average_duration,
            commands_run=commands_run,
            unique_users=unique_users,
            previous_period_change_percent=previous_change,
        ),
        timeline=_timeline(
            timeline_rows,
            starts_at=starts_at,
            ends_at=ends_at,
            granularity=granularity,
        ),
        tools=tools,
        command_groups=command_groups,
    )


def _encode_cursor(row: McpCallLog) -> str:
    data = json.dumps(
        {"created_at": row.created_at.isoformat(), "id": str(row.id)},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        created_at = datetime.fromisoformat(payload["created_at"])
        row_id = uuid.UUID(payload["id"])
        if created_at.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="مؤشر السجل غير صالح.") from exc
    return created_at, row_id


def _actor(user: User | None) -> McpCallActorRead | None:
    if not user:
        return None
    return McpCallActorRead(id=user.id, email=user.email, full_name=user.full_name)


def _list_item(row: McpCallLog, user: User | None) -> McpCallListItem:
    return McpCallListItem(
        id=row.id,
        created_at=row.created_at,
        actor=_actor(user),
        trace_id=row.trace_id,
        tool_name=row.tool_name,
        command_name=row.command_name,
        status=row.status,
        duration_ms=row.duration_ms,
    )


def list_calls(
    db: Session,
    *,
    period: McpAnalyticsPeriod,
    tool_name: str | None = None,
    command_name: str | None = None,
    status: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    now: datetime | None = None,
) -> McpCallListRead:
    ends_at = now or datetime.now(UTC)
    starts_at, _ = _period_bounds(period, now=ends_at)
    conditions = [
        McpCallLog.created_at >= starts_at,
        McpCallLog.created_at <= ends_at,
    ]
    if tool_name:
        conditions.append(McpCallLog.tool_name == tool_name)
    if command_name:
        conditions.append(McpCallLog.command_name == command_name)
    if status:
        conditions.append(McpCallLog.status == status)
    if cursor:
        cursor_time, cursor_id = _decode_cursor(cursor)
        conditions.append(
            or_(
                McpCallLog.created_at < cursor_time,
                and_(
                    McpCallLog.created_at == cursor_time,
                    McpCallLog.id < cursor_id,
                ),
            )
        )

    rows = db.execute(
        select(McpCallLog, User)
        .outerjoin(User, User.id == McpCallLog.user_id)
        .where(*conditions)
        .order_by(McpCallLog.created_at.desc(), McpCallLog.id.desc())
        .limit(limit + 1)
    ).all()
    has_more = len(rows) > limit
    visible = rows[:limit]
    return McpCallListRead(
        items=[_list_item(row, user) for row, user in visible],
        next_cursor=_encode_cursor(visible[-1][0]) if has_more and visible else None,
    )


def get_call(
    db: Session,
    call_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> McpCallDetailRead:
    retention_cutoff = (now or datetime.now(UTC)) - timedelta(
        days=MCP_LOG_RETENTION_DAYS
    )
    result = db.execute(
        select(McpCallLog, User)
        .outerjoin(User, User.id == McpCallLog.user_id)
        .where(
            McpCallLog.id == call_id,
            McpCallLog.created_at >= retention_cutoff,
        )
    ).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="سجل الاستدعاء غير موجود.")
    row, user = result
    return McpCallDetailRead(
        **_list_item(row, user).model_dump(),
        input=row.input_json,
        output=row.output_json,
        error=row.error,
    )


def delete_expired_logs(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    cutoff = (now or datetime.now(UTC)) - timedelta(days=MCP_LOG_RETENTION_DAYS)
    result = db.execute(delete(McpCallLog).where(McpCallLog.created_at < cutoff))
    db.commit()
    return int(result.rowcount or 0)
