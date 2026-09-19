"""add cached draft revision change summaries

Revision ID: 021_revision_summaries
Revises: 020_minimize_donations
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_revision_summaries"
down_revision: Union[str, None] = "020_minimize_donations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "draft_revision_change_summaries",
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "schema_version >= 1",
            name="ck_draft_revision_change_summary_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["article_draft_revisions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("revision_id"),
    )


def downgrade() -> None:
    op.drop_table("draft_revision_change_summaries")
