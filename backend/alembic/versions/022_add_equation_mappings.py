"""add article equation mappings

Revision ID: 022_equation_mappings
Revises: 021_revision_summaries
Create Date: 2026-09-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_equation_mappings"
down_revision: Union[str, None] = "021_revision_summaries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column(
            "equation_mappings",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("articles", "equation_mappings")
