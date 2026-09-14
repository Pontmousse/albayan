"""bind compile attempts to article sessions

Revision ID: 015_session_compile
Revises: 014_mcp_call_logs
Create Date: 2026-09-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_session_compile"
down_revision: Union[str, None] = "014_mcp_call_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "article_versions",
        sa.Column("active_compile_session_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("active_compile_session_revision", sa.Integer(), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("compiled_session_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("compiled_session_revision", sa.Integer(), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("compile_error_code", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("compile_error_message", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "ck_article_versions_active_compile_session_revision_nonnegative",
        "article_versions",
        "active_compile_session_revision IS NULL OR active_compile_session_revision >= 0",
    )
    op.create_check_constraint(
        "ck_article_versions_compiled_session_revision_nonnegative",
        "article_versions",
        "compiled_session_revision IS NULL OR compiled_session_revision >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_article_versions_compiled_session_revision_nonnegative",
        "article_versions",
        type_="check",
    )
    op.drop_constraint(
        "ck_article_versions_active_compile_session_revision_nonnegative",
        "article_versions",
        type_="check",
    )
    op.drop_column("article_versions", "compile_error_message")
    op.drop_column("article_versions", "compile_error_code")
    op.drop_column("article_versions", "compiled_session_revision")
    op.drop_column("article_versions", "compiled_session_id")
    op.drop_column("article_versions", "active_compile_session_revision")
    op.drop_column("article_versions", "active_compile_session_id")
