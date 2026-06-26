"""create articles tables

Revision ID: 002_create_articles
Revises: 001_create_users
Create Date: 2026-06-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_create_articles"
down_revision: Union[str, None] = "001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

article_status = sa.Enum(
    "draft",
    "submitted",
    "under_review",
    "accepted",
    "rejected",
    "published",
    name="articlestatus",
    native_enum=False,
)
reviewer_assignment_status = sa.Enum(
    "invited",
    "accepted",
    "declined",
    "completed",
    name="reviewerassignmentstatus",
    native_enum=False,
)
source_type = sa.Enum(
    "zip_upload",
    "web_editor",
    name="sourcetype",
    native_enum=False,
)
compile_status = sa.Enum(
    "pending",
    "processing",
    "success",
    "failed",
    name="compilestatus",
    native_enum=False,
)
review_recommendation = sa.Enum(
    "accept",
    "minor_revision",
    "major_revision",
    "reject",
    name="reviewrecommendation",
    native_enum=False,
)
review_status = sa.Enum(
    "draft",
    "submitted",
    name="reviewstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("submitted_by", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column(
            "status",
            article_status,
            nullable=False,
            server_default="draft",
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
        sa.ForeignKeyConstraint(
            ["submitted_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_articles_submitted_by", "articles", ["submitted_by"])
    op.create_index("ix_articles_status", "articles", ["status"])

    op.create_table(
        "article_versions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_prefix", sa.String(length=500), nullable=False),
        sa.Column(
            "source_type",
            source_type,
            nullable=False,
            server_default="zip_upload",
        ),
        sa.Column(
            "compile_status",
            compile_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "article_id",
            "version_number",
            name="uq_article_versions_article_version",
        ),
    )
    op.create_index(
        "ix_article_versions_article_id", "article_versions", ["article_id"]
    )

    op.create_table(
        "article_authors",
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("author_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "is_corresponding",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("article_id", "user_id"),
    )

    op.create_table(
        "article_reviewers",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            reviewer_assignment_status,
            nullable=False,
            server_default="invited",
        ),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "article_id",
            "user_id",
            name="uq_article_reviewers_article_user",
        ),
    )
    op.create_index(
        "ix_article_reviewers_article_id", "article_reviewers", ["article_id"]
    )
    op.create_index(
        "ix_article_reviewers_user_id", "article_reviewers", ["user_id"]
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("article_reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("article_version_id", sa.Uuid(), nullable=False),
        sa.Column("comments_to_author", sa.Text(), nullable=True),
        sa.Column("comments_to_editor", sa.Text(), nullable=True),
        sa.Column("recommendation", review_recommendation, nullable=True),
        sa.Column(
            "status",
            review_status,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["article_reviewer_id"],
            ["article_reviewers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["article_version_id"],
            ["article_versions.id"],
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_reviews_article_reviewer_id", "reviews", ["article_reviewer_id"]
    )
    op.create_index(
        "ix_reviews_article_version_id", "reviews", ["article_version_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_reviews_article_version_id", table_name="reviews")
    op.drop_index("ix_reviews_article_reviewer_id", table_name="reviews")
    op.drop_table("reviews")

    op.drop_index("ix_article_reviewers_user_id", table_name="article_reviewers")
    op.drop_index("ix_article_reviewers_article_id", table_name="article_reviewers")
    op.drop_table("article_reviewers")

    op.drop_table("article_authors")

    op.drop_index("ix_article_versions_article_id", table_name="article_versions")
    op.drop_table("article_versions")

    op.drop_index("ix_articles_status", table_name="articles")
    op.drop_index("ix_articles_submitted_by", table_name="articles")
    op.drop_table("articles")

    op.drop_column("users", "is_admin")
