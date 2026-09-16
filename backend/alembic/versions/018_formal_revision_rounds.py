"""add formal version review rounds and revision requests

Revision ID: 018_formal_rounds
Revises: 017_draft_history
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_formal_rounds"
down_revision: Union[str, None] = "017_draft_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 016 sized this non-native enum from its then-longest value (13 chars).
    # `revision_request` needs 16 characters.
    op.alter_column(
        "article_draft_revisions",
        "reason",
        existing_type=sa.String(length=13),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
    op.add_column("articles", sa.Column("revision_request_note", sa.Text(), nullable=True))
    op.add_column(
        "articles",
        sa.Column("revision_requested_for_version_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "articles", sa.Column("revision_requested_by", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "articles",
        sa.Column("revision_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_articles_revision_requested_version",
        "articles",
        "article_versions",
        ["revision_requested_for_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_articles_revision_requested_by",
        "articles",
        "users",
        ["revision_requested_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_unique_constraint(
        "uq_article_versions_id_article", "article_versions", ["id", "article_id"]
    )
    op.add_column(
        "article_reviewers", sa.Column("article_version_id", sa.Uuid(), nullable=True)
    )
    op.execute(
        """
        UPDATE article_reviewers AS assignment
        SET article_version_id = COALESCE(
          (
            SELECT review.article_version_id
            FROM reviews AS review
            JOIN article_versions AS reviewed_version
              ON reviewed_version.id = review.article_version_id
            WHERE review.article_reviewer_id = assignment.id
              AND reviewed_version.article_id = assignment.article_id
            ORDER BY reviewed_version.version_number DESC
            LIMIT 1
          ),
          (
            SELECT version.id
            FROM article_versions AS version
            WHERE version.article_id = assignment.article_id
            ORDER BY version.version_number DESC
            LIMIT 1
          )
        )
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM article_reviewers WHERE article_version_id IS NULL
          ) THEN
            RAISE EXCEPTION 'reviewer assignment has no formal article version';
          END IF;
        END $$
        """
    )
    op.alter_column("article_reviewers", "article_version_id", nullable=False)
    op.create_index(
        "ix_article_reviewers_article_version_id",
        "article_reviewers",
        ["article_version_id"],
    )
    op.drop_constraint(
        "uq_article_reviewers_article_user", "article_reviewers", type_="unique"
    )
    op.create_unique_constraint(
        "uq_article_reviewers_version_user",
        "article_reviewers",
        ["article_version_id", "user_id"],
    )
    op.create_unique_constraint(
        "uq_article_reviewers_id_version",
        "article_reviewers",
        ["id", "article_version_id"],
    )
    op.create_foreign_key(
        "fk_article_reviewers_version_article",
        "article_reviewers",
        "article_versions",
        ["article_version_id", "article_id"],
        ["id", "article_id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "reviews",
        sa.Column(
            "reveal_reviewer_identity_to_author",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_unique_constraint(
        "uq_reviews_assignment_version",
        "reviews",
        ["article_reviewer_id", "article_version_id"],
    )
    op.drop_constraint(
        "reviews_article_reviewer_id_fkey", "reviews", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_reviews_assignment_version",
        "reviews",
        "article_reviewers",
        ["article_reviewer_id", "article_version_id"],
        ["id", "article_version_id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "invitations", sa.Column("article_version_id", sa.Uuid(), nullable=True)
    )
    # The ORM-backed enum persists member names. Normalize any rows inserted
    # directly with the lowercase defaults from migration 005.
    op.execute("UPDATE invitations SET role = upper(role), status = upper(status)")
    op.alter_column(
        "invitations", "status", server_default="PENDING", existing_nullable=False
    )
    op.execute(
        """
        UPDATE invitations AS invitation
        SET article_version_id = (
          SELECT version.id
          FROM article_versions AS version
          WHERE version.article_id = invitation.article_id
          ORDER BY version.version_number DESC
          LIMIT 1
        )
        WHERE invitation.role = 'REVIEWER'
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM invitations
            WHERE role = 'REVIEWER' AND article_version_id IS NULL
          ) THEN
            RAISE EXCEPTION 'reviewer invitation has no formal article version';
          END IF;
        END $$
        """
    )
    op.create_index(
        "ix_invitations_article_version_id", "invitations", ["article_version_id"]
    )
    op.create_check_constraint(
        "ck_invitations_reviewer_version",
        "invitations",
        "(role = 'REVIEWER' AND article_version_id IS NOT NULL) OR "
        "(role = 'EDITOR' AND article_version_id IS NULL)",
    )
    op.create_foreign_key(
        "fk_invitations_version_article",
        "invitations",
        "article_versions",
        ["article_version_id", "article_id"],
        ["id", "article_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_invitations_version_article", "invitations", type_="foreignkey"
    )
    op.drop_constraint(
        "ck_invitations_reviewer_version", "invitations", type_="check"
    )
    op.drop_index("ix_invitations_article_version_id", table_name="invitations")
    op.drop_column("invitations", "article_version_id")

    op.drop_constraint("fk_reviews_assignment_version", "reviews", type_="foreignkey")
    op.create_foreign_key(
        "reviews_article_reviewer_id_fkey",
        "reviews",
        "article_reviewers",
        ["article_reviewer_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("uq_reviews_assignment_version", "reviews", type_="unique")
    op.drop_column("reviews", "reveal_reviewer_identity_to_author")

    op.drop_constraint(
        "fk_article_reviewers_version_article",
        "article_reviewers",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_article_reviewers_id_version", "article_reviewers", type_="unique"
    )
    op.drop_constraint(
        "uq_article_reviewers_version_user", "article_reviewers", type_="unique"
    )
    op.create_unique_constraint(
        "uq_article_reviewers_article_user",
        "article_reviewers",
        ["article_id", "user_id"],
    )
    op.drop_index(
        "ix_article_reviewers_article_version_id", table_name="article_reviewers"
    )
    op.drop_column("article_reviewers", "article_version_id")
    op.drop_constraint(
        "uq_article_versions_id_article", "article_versions", type_="unique"
    )

    op.drop_constraint(
        "fk_articles_revision_requested_by", "articles", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_articles_revision_requested_version", "articles", type_="foreignkey"
    )
    op.drop_column("articles", "revision_requested_at")
    op.drop_column("articles", "revision_requested_by")
    op.drop_column("articles", "revision_requested_for_version_id")
    op.drop_column("articles", "revision_request_note")
    # Keep the harmless widened VARCHAR so structural downgrade remains possible
    # even when historical revision_request rows exist.
