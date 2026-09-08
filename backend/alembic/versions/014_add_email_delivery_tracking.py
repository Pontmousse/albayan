"""add transactional email delivery tracking

Revision ID: 014_email_delivery_tracking
Revises: 013_user_gender
Create Date: 2026-09-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_email_delivery_tracking"
down_revision: Union[str, None] = "013_user_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_email_id", sa.String(length=255), nullable=True),
        sa.Column("email_kind", sa.String(length=120), nullable=False),
        sa.Column("recipient_hash", sa.String(length=64), nullable=False),
        sa.Column("event_scope", sa.String(length=120), nullable=True),
        sa.Column("related_id", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=True),
        sa.Column("provider_accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_state", sa.String(length=32), nullable=False),
        sa.Column("latest_provider_event", sa.String(length=80), nullable=True),
        sa.Column("latest_provider_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=160), nullable=True),
        sa.Column("failure_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_email_id"),
    )
    op.create_index("ix_email_deliveries_provider_email_id", "email_deliveries", ["provider_email_id"])
    op.create_index("ix_email_deliveries_email_kind", "email_deliveries", ["email_kind"])
    op.create_index("ix_email_deliveries_recipient_hash", "email_deliveries", ["recipient_hash"])
    op.create_index("ix_email_deliveries_related_id", "email_deliveries", ["related_id"])
    op.create_index("ix_email_deliveries_latest_state", "email_deliveries", ["latest_state"])
    op.create_index(
        "ix_email_deliveries_context",
        "email_deliveries",
        ["email_kind", "related_id", "created_at"],
    )

    op.create_table(
        "email_delivery_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("provider_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["delivery_id"], ["email_deliveries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_event_id"),
    )
    op.create_index("ix_email_delivery_events_delivery_id", "email_delivery_events", ["delivery_id"])
    op.create_index("ix_email_delivery_events_provider_event_id", "email_delivery_events", ["provider_event_id"])


def downgrade() -> None:
    op.drop_index("ix_email_delivery_events_provider_event_id", table_name="email_delivery_events")
    op.drop_index("ix_email_delivery_events_delivery_id", table_name="email_delivery_events")
    op.drop_table("email_delivery_events")
    op.drop_index("ix_email_deliveries_context", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_latest_state", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_related_id", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_recipient_hash", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_email_kind", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_provider_email_id", table_name="email_deliveries")
    op.drop_table("email_deliveries")
