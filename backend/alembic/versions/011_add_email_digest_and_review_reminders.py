"""add email digest state and review reminder fields

Revision ID: 011_email_digest_review_reminders
Revises: 010_account_deletion_requests
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_email_digest_review_reminders"
down_revision: Union[str, None] = "010_account_deletion_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "article_reviewers",
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "invitations",
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "article_reviewers",
        sa.Column("reminder_midpoint_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "article_reviewers",
        sa.Column("reminder_due_soon_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_article_reviewers_review_due_at",
        "article_reviewers",
        ["review_due_at"],
    )

    op.create_table(
        "email_digest_states",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "last_unread_digest_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("email_digest_states")
    op.drop_column("invitations", "review_due_at")
    op.drop_index("ix_article_reviewers_review_due_at", table_name="article_reviewers")
    op.drop_column("article_reviewers", "reminder_due_soon_sent_at")
    op.drop_column("article_reviewers", "reminder_midpoint_sent_at")
    op.drop_column("article_reviewers", "review_due_at")
