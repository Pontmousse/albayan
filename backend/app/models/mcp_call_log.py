import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class McpCallLog(Base):
    __tablename__ = "mcp_call_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'error')",
            name="ck_mcp_call_logs_status",
        ),
        CheckConstraint(
            "duration_ms >= 0",
            name="ck_mcp_call_logs_duration_nonnegative",
        ),
        Index("ix_mcp_call_logs_created_at", "created_at"),
        Index("ix_mcp_call_logs_tool_created_at", "tool_name", "created_at"),
        Index(
            "ix_mcp_call_logs_command_created_at",
            "command_name",
            "created_at",
        ),
        Index("ix_mcp_call_logs_status_created_at", "status", "created_at"),
        Index("ix_mcp_call_logs_user_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    trace_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(100))
    command_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    duration_ms: Mapped[int] = mapped_column(Integer)
    input_json: Mapped[dict[str, Any]] = mapped_column("input", JSONB)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(
        "output", JSONB, nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
