"""create users table

Revision ID: 001_create_users
Revises:
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("clerk_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("affiliation", sa.String(length=300), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_clerk_id", table_name="users")
    op.drop_table("users")
