"""Persist article unit conventions and historical snapshots.

Revision ID: 023_unit_conventions
Revises: 022_equation_mappings
Create Date: 2026-10-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_unit_conventions"
down_revision: Union[str, None] = "022_equation_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EMPTY = sa.text("""'{"overrides": {}, "custom_units": {}}'""")


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("unit_conventions", sa.JSON(), nullable=False, server_default=_EMPTY),
    )
    # Legacy revisions retain an immutable empty snapshot. Only future revisions
    # capture the article-specific settings in effect when they are saved.
    op.add_column(
        "article_draft_revisions",
        sa.Column("unit_conventions", sa.JSON(), nullable=False, server_default=_EMPTY),
    )
    # Formal versions outlive pruned draft revisions; snapshot their conventions too.
    op.add_column(
        "article_versions",
        sa.Column("unit_conventions", sa.JSON(), nullable=False, server_default=_EMPTY),
    )


def downgrade() -> None:
    op.drop_column("article_versions", "unit_conventions")
    op.drop_column("article_draft_revisions", "unit_conventions")
    op.drop_column("articles", "unit_conventions")
