"""move status to article_versions

Revision ID: 003_version_status
Revises: 002_create_articles
Create Date: 2026-06-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_version_status"
down_revision: Union[str, None] = "002_create_articles"
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
source_type = sa.Enum(
    "zip_upload",
    "web_editor",
    name="sourcetype",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column(
        "article_versions",
        sa.Column("status", article_status, nullable=True),
    )

    op.execute(
        """
        UPDATE article_versions av
        SET status = a.status
        FROM articles a
        WHERE av.article_id = a.id
          AND av.version_number = (
            SELECT MAX(version_number)
            FROM article_versions
            WHERE article_id = a.id
          )
        """
    )

    op.execute(
        """
        INSERT INTO article_versions (
            id,
            article_id,
            version_number,
            storage_prefix,
            source_type,
            compile_status,
            status,
            created_at
        )
        SELECT
            gen_random_uuid(),
            a.id,
            1,
            'articles/' || a.id::text || '/versions/v1/',
            'web_editor',
            'pending',
            a.status,
            now()
        FROM articles a
        WHERE NOT EXISTS (
            SELECT 1 FROM article_versions v WHERE v.article_id = a.id
        )
        """
    )

    op.alter_column(
        "article_versions",
        "status",
        existing_type=article_status,
        nullable=False,
        server_default="draft",
    )

    op.create_index(
        "ix_article_versions_status",
        "article_versions",
        ["status"],
    )

    op.drop_index("ix_articles_status", table_name="articles")
    op.drop_column("articles", "status")

    op.alter_column(
        "article_versions",
        "source_type",
        existing_type=source_type,
        server_default="web_editor",
    )


def downgrade() -> None:
    op.alter_column(
        "article_versions",
        "source_type",
        existing_type=source_type,
        server_default="zip_upload",
    )

    op.add_column(
        "articles",
        sa.Column("status", article_status, nullable=True),
    )

    op.execute(
        """
        UPDATE articles a
        SET status = av.status
        FROM article_versions av
        WHERE av.article_id = a.id
          AND av.version_number = (
            SELECT MAX(version_number)
            FROM article_versions
            WHERE article_id = a.id
          )
        """
    )

    op.execute(
        """
        UPDATE articles
        SET status = 'draft'
        WHERE status IS NULL
        """
    )

    op.alter_column(
        "articles",
        "status",
        existing_type=article_status,
        nullable=False,
        server_default="draft",
    )

    op.create_index("ix_articles_status", "articles", ["status"])

    op.drop_index("ix_article_versions_status", table_name="article_versions")
    op.drop_column("article_versions", "status")
