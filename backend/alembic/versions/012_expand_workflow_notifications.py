"""expand workflow notifications

Revision ID: 012_workflow_notifications
Revises: 011_email_digest_reminders
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_workflow_notifications"
down_revision: Union[str, None] = "011_email_digest_reminders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.String(length=20),
        type_=sa.String(length=48),
        existing_nullable=False,
    )
    op.add_column(
        "notifications",
        sa.Column("event_key", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "ix_notifications_event_key",
        "notifications",
        ["event_key"],
        unique=True,
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM notifications WHERE type NOT IN "
        "('SYSTEM', 'MENTION', 'ISSUE_REPLY', 'ISSUE_UPVOTED', "
        "'ISSUE_STATUS_CHANGED')"
    )
    op.drop_index("ix_notifications_event_key", table_name="notifications")
    op.drop_column("notifications", "event_key")
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.String(length=48),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
