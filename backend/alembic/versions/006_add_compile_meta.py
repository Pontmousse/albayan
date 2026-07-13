"""add compile metadata to article_versions

Revision ID: 006_compile_meta
Revises: 005_invitations
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_compile_meta"
down_revision: Union[str, None] = "005_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "article_versions",
        sa.Column("active_compile_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "article_versions",
        sa.Column("compiled_document_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("article_versions", "compiled_document_hash")
    op.drop_column("article_versions", "active_compile_id")
