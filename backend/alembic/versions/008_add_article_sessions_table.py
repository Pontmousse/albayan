"""add article_sessions table

Revision ID: 008_article_sessions
Revises: 007_agent_tokens
Create Date: 2026-08-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_article_sessions"
down_revision: Union[str, None] = "007_agent_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("article_version_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_saved_revision", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["article_version_id"], ["article_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("article_id", name="uq_article_sessions_article"),
    )
    op.create_index("ix_article_sessions_article_id", "article_sessions", ["article_id"])
    op.create_index(
        "ix_article_sessions_article_version_id",
        "article_sessions",
        ["article_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_article_sessions_article_version_id", table_name="article_sessions"
    )
    op.drop_index("ix_article_sessions_article_id", table_name="article_sessions")
    op.drop_table("article_sessions")
