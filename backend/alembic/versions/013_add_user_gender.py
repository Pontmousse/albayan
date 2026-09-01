"""add immutable user gender

Revision ID: 013_user_gender
Revises: 012_workflow_notifications
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_user_gender"
down_revision: Union[str, None] = "012_workflow_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("gender", sa.String(length=6), nullable=True),
    )
    op.create_check_constraint(
        "ck_users_gender",
        "users",
        "gender IS NULL OR gender IN ('male', 'female')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_gender", "users", type_="check")
    op.drop_column("users", "gender")
