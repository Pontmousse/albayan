"""add notifications and issues

Revision ID: 009_notifications_issues
Revises: 008_article_sessions
Create Date: 2026-08-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_notifications_issues"
down_revision: Union[str, None] = "008_article_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

notification_type = sa.Enum(
    "system",
    "mention",
    "issue_reply",
    "issue_upvoted",
    "issue_status_changed",
    name="notificationtype",
    native_enum=False,
)
issue_status = sa.Enum(
    "open",
    "in_progress",
    "resolved",
    "closed",
    name="issuestatus",
    native_enum=False,
)
issue_category = sa.Enum(
    "bug",
    "feature_request",
    "feedback",
    name="issuecategory",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_notifications_user_created_at",
        "notifications",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_notifications_user_is_read",
        "notifications",
        ["user_id", "is_read"],
    )
    op.create_index("ix_notifications_actor_id", "notifications", ["actor_id"])

    op.create_table(
        "issues",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            issue_status,
            nullable=False,
            server_default="open",
        ),
        sa.Column("category", issue_category, nullable=False),
        sa.Column(
            "upvote_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_issues_user_id", "issues", ["user_id"])
    op.create_index("ix_issues_created_at", "issues", ["created_at"])
    op.create_index(
        "ix_issues_user_created_at", "issues", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_issues_status_created_at", "issues", ["status", "created_at"]
    )
    op.create_index(
        "ix_issues_category_created_at", "issues", ["category", "created_at"]
    )

    op.create_table(
        "issue_upvotes",
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("issue_id", "user_id"),
        sa.UniqueConstraint(
            "issue_id", "user_id", name="uq_issue_upvotes_issue_user"
        ),
    )

    op.create_table(
        "issue_images",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("s3_key", sa.String(length=500), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "issue_id", "position", name="uq_issue_images_issue_position"
        ),
    )
    op.create_index("ix_issue_images_issue_id", "issue_images", ["issue_id"])


def downgrade() -> None:
    op.drop_index("ix_issue_images_issue_id", table_name="issue_images")
    op.drop_table("issue_images")
    op.drop_table("issue_upvotes")
    op.drop_index("ix_issues_category_created_at", table_name="issues")
    op.drop_index("ix_issues_status_created_at", table_name="issues")
    op.drop_index("ix_issues_user_created_at", table_name="issues")
    op.drop_index("ix_issues_created_at", table_name="issues")
    op.drop_index("ix_issues_user_id", table_name="issues")
    op.drop_table("issues")
    op.drop_index("ix_notifications_actor_id", table_name="notifications")
    op.drop_index("ix_notifications_user_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_created_at", table_name="notifications")
    op.drop_table("notifications")
