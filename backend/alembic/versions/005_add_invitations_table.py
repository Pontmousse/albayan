"""add invitations table

Revision ID: 005_invitations
Revises: 004_article_editors
Create Date: 2026-07-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_invitations"
down_revision: Union[str, None] = "004_article_editors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

invitation_role = sa.Enum(
    "reviewer",
    "editor",
    name="invitationrole",
    native_enum=False,
)
invitation_status = sa.Enum(
    "pending",
    "accepted",
    "expired",
    "cancelled",
    name="invitationstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("role", invitation_role, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            invitation_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("token", name="uq_invitations_token"),
    )
    op.create_index("ix_invitations_article_id", "invitations", ["article_id"])
    op.create_index("ix_invitations_email", "invitations", ["email"])
    op.create_index("ix_invitations_token", "invitations", ["token"], unique=True)
    op.create_index("ix_invitations_invited_by", "invitations", ["invited_by"])


def downgrade() -> None:
    op.drop_index("ix_invitations_invited_by", table_name="invitations")
    op.drop_index("ix_invitations_token", table_name="invitations")
    op.drop_index("ix_invitations_email", table_name="invitations")
    op.drop_index("ix_invitations_article_id", table_name="invitations")
    op.drop_table("invitations")
