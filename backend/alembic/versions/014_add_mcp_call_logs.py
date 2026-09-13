"""add MCP call logs

Revision ID: 014_mcp_call_logs
Revises: 013_user_gender
Create Date: 2026-09-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "014_mcp_call_logs"
down_revision: Union[str, None] = "013_user_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_call_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("command_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("input", JSONB(), nullable=False),
        sa.Column("output", JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('success', 'error')",
            name="ck_mcp_call_logs_status",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0",
            name="ck_mcp_call_logs_duration_nonnegative",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mcp_call_logs_created_at", "mcp_call_logs", ["created_at"]
    )
    op.create_index(
        "ix_mcp_call_logs_tool_created_at",
        "mcp_call_logs",
        ["tool_name", "created_at"],
    )
    op.create_index(
        "ix_mcp_call_logs_command_created_at",
        "mcp_call_logs",
        ["command_name", "created_at"],
    )
    op.create_index(
        "ix_mcp_call_logs_status_created_at",
        "mcp_call_logs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_mcp_call_logs_user_created_at",
        "mcp_call_logs",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_mcp_call_logs_user_created_at", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_status_created_at", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_command_created_at", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_tool_created_at", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_created_at", table_name="mcp_call_logs")
    op.drop_table("mcp_call_logs")
