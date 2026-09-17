"""minimize donation state to email receipt deduplication only

Revision ID: 020_minimize_donations
Revises: 019_donations
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_minimize_donations"
down_revision: Union[str, None] = "019_donations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_stripe_webhook_events_processed_at", table_name="stripe_webhook_events")
    op.drop_table("stripe_webhook_events")
    op.drop_index("ix_donations_status_created_at", table_name="donations")
    op.drop_index("ix_donations_created_at", table_name="donations")
    op.drop_table("donations")

    op.create_table(
        "donation_email_receipts",
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=False),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("stripe_checkout_session_id"),
    )


def downgrade() -> None:
    op.drop_table("donation_email_receipts")

    op.create_table(
        "donations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("donor_email", sa.String(length=320), nullable=True),
        sa.Column("confirmation_email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_donations_amount_positive"),
        sa.CheckConstraint("status IN ('pending', 'paid', 'failed', 'expired')", name="ck_donations_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_checkout_session_id", name="uq_donations_stripe_checkout_session_id"),
        sa.UniqueConstraint("stripe_payment_intent_id", name="uq_donations_stripe_payment_intent_id"),
    )
    op.create_index("ix_donations_created_at", "donations", ["created_at"])
    op.create_index("ix_donations_status_created_at", "donations", ["status", "created_at"])

    op.create_table(
        "stripe_webhook_events",
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_stripe_webhook_events_processed_at", "stripe_webhook_events", ["processed_at"])
