"""add account deletion requests

Revision ID: 010_account_deletion_requests
Revises: 009_notifications_issues
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_account_deletion_requests"
down_revision: Union[str, None] = "009_notifications_issues"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email_snapshot", sa.String(length=320), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_account_deletion_requests_user_id",
        "account_deletion_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_account_deletion_requests_email_snapshot",
        "account_deletion_requests",
        ["email_snapshot"],
    )
    op.create_index(
        "ix_account_deletion_requests_status",
        "account_deletion_requests",
        ["status"],
    )
    op.create_index(
        "ix_account_deletion_requests_requested_at",
        "account_deletion_requests",
        ["requested_at"],
    )
    op.create_index(
        "ix_account_deletion_requests_reviewed_by",
        "account_deletion_requests",
        ["reviewed_by"],
    )


def downgrade() -> None:
    op.drop_index("ix_account_deletion_requests_reviewed_by")
    op.drop_index("ix_account_deletion_requests_requested_at")
    op.drop_index("ix_account_deletion_requests_status")
    op.drop_index("ix_account_deletion_requests_email_snapshot")
    op.drop_index("ix_account_deletion_requests_user_id")
    op.drop_table("account_deletion_requests")
