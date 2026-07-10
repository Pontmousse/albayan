"""add article editors table

Revision ID: 004_article_editors
Revises: 003_version_status
Create Date: 2026-07-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_article_editors"
down_revision: Union[str, None] = "003_version_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_editors",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("assigned_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "article_id",
            "user_id",
            name="uq_article_editors_article_user",
        ),
    )
    op.create_index(
        "ix_article_editors_article_id", "article_editors", ["article_id"]
    )
    op.create_index("ix_article_editors_user_id", "article_editors", ["user_id"])
    op.create_index(
        "ix_article_editors_assigned_by", "article_editors", ["assigned_by"]
    )


def downgrade() -> None:
    op.drop_index("ix_article_editors_assigned_by", table_name="article_editors")
    op.drop_index("ix_article_editors_user_id", table_name="article_editors")
    op.drop_index("ix_article_editors_article_id", table_name="article_editors")
    op.drop_table("article_editors")
