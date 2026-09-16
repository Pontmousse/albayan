"""replace mutable article sessions with immutable draft revisions

Revision ID: 016_draft_revisions
Revises: 015_session_compile
Create Date: 2026-09-15

This is intentionally destructive for article-domain development data. Account,
role, issue, and agent-token rows are preserved. The downgrade restores only the
old structure; deleted article data cannot be recovered.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_draft_revisions"
down_revision: Union[str, None] = "015_session_compile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reviews point at versions with RESTRICT; all other article-owned rows cascade.
    op.execute("DELETE FROM reviews")
    op.execute("DELETE FROM notifications WHERE metadata ->> 'article_id' IS NOT NULL")
    op.execute(
        "DELETE FROM mcp_call_logs WHERE tool_name IN "
        "('get_article_session', 'save_session', 'apply_document_command', "
        "'get_document_outline', 'get_document_blocks', 'compile_article')"
    )
    op.execute("DELETE FROM articles")
    op.execute(
        """
        UPDATE agent_tokens
        SET scopes = (
          SELECT COALESCE(jsonb_agg(DISTINCT
            CASE WHEN value = 'articles:session:write'
                 THEN 'articles:draft:write' ELSE value END
          ), '[]'::jsonb)
          FROM jsonb_array_elements_text(agent_tokens.scopes) AS scope(value)
        )
        WHERE scopes ? 'articles:session:write'
        """
    )
    op.execute(
        """
        CREATE FUNCTION protect_formal_article_version() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'formal article versions are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_protect_formal_article_version
        BEFORE UPDATE ON article_versions
        FOR EACH ROW EXECUTE FUNCTION protect_formal_article_version();
        """
    )

    op.drop_table("article_sessions")

    article_status = sa.Enum(
        "draft", "submitted", "under_review", "revision_requested",
        "accepted", "rejected", "published",
        name="articlestatus", native_enum=False,
    )
    actor_type = sa.Enum(
        "human", "agent", "system", name="draftactortype", native_enum=False
    )
    revision_reason = sa.Enum(
        "initial", "autosave", "ai_edit", "metadata_edit", "restore",
        name="draftrevisionreason", native_enum=False,
    )
    compile_status = sa.Enum(
        "pending", "processing", "success", "failed",
        name="compilestatus", native_enum=False,
    )

    op.add_column(
        "articles",
        sa.Column("status", article_status, nullable=False, server_default="draft"),
    )
    op.add_column(
        "articles",
        sa.Column("draft_revision_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_articles_draft_revision_number_nonnegative",
        "articles",
        "draft_revision_number >= 0",
    )
    op.create_index("ix_articles_status", "articles", ["status"])

    op.create_table(
        "article_draft_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=700), nullable=False),
        sa.Column("document_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("actor_type", actor_type, nullable=False),
        sa.Column("reason", revision_reason, nullable=False),
        sa.Column("restored_from_id", sa.Uuid(), nullable=True),
        sa.Column("compile_status", compile_status, nullable=False, server_default="pending"),
        sa.Column("active_compile_id", sa.Uuid(), nullable=True),
        sa.Column("compile_error_code", sa.String(length=100), nullable=True),
        sa.Column("compile_error_message", sa.Text(), nullable=True),
        sa.Column("compiled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("revision_number >= 1", name="ck_draft_revision_number_positive"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "revision_number", name="uq_draft_revision_article_number"),
        sa.UniqueConstraint("storage_key", name="uq_draft_revision_storage_key"),
    )
    op.create_index(
        "ix_article_draft_revisions_article_id", "article_draft_revisions", ["article_id"]
    )

    op.add_column("articles", sa.Column("current_draft_revision_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_articles_current_draft_revision",
        "articles", "article_draft_revisions",
        ["current_draft_revision_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index(
        "ix_articles_current_draft_revision_id", "articles", ["current_draft_revision_id"]
    )

    op.drop_constraint(
        "ck_article_versions_active_compile_session_revision_nonnegative",
        "article_versions", type_="check",
    )
    op.drop_constraint(
        "ck_article_versions_compiled_session_revision_nonnegative",
        "article_versions", type_="check",
    )
    op.drop_index("ix_article_versions_status", table_name="article_versions")
    for column in (
        "status", "compile_status", "active_compile_id",
        "active_compile_session_id", "active_compile_session_revision",
        "compiled_document_hash", "compiled_session_id", "compiled_session_revision",
        "compile_error_code", "compile_error_message",
    ):
        op.drop_column("article_versions", column)
    op.drop_column("article_versions", "change_summary")
    op.add_column("article_versions", sa.Column("source_draft_revision_id", sa.Uuid(), nullable=True))
    op.add_column("article_versions", sa.Column("document_hash", sa.String(length=64), nullable=False))
    op.add_column("article_versions", sa.Column("title_snapshot", sa.String(length=500), nullable=False))
    op.add_column("article_versions", sa.Column("abstract_snapshot", sa.Text(), nullable=True))
    op.create_index(
        "ix_article_versions_source_draft_revision_id",
        "article_versions", ["source_draft_revision_id"],
    )

    op.create_table(
        "draft_command_receipts",
        sa.Column("command_id", sa.Uuid(), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("base_revision", sa.Integer(), nullable=False),
        sa.Column("result_revision_id", sa.Uuid(), nullable=True),
        sa.Column("result_revision_number", sa.Integer(), nullable=False),
        sa.Column("affected_block_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["result_revision_id"], ["article_draft_revisions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("command_id"),
    )
    op.create_index(
        "ix_draft_command_receipts_article_id", "draft_command_receipts", ["article_id"]
    )

    # Only compile bookkeeping may change after a snapshot row is inserted.
    op.execute(
        """
        CREATE FUNCTION protect_draft_revision_snapshot() RETURNS trigger AS $$
        BEGIN
          IF ROW(NEW.id, NEW.article_id, NEW.revision_number, NEW.storage_key,
                 NEW.document_hash, NEW.created_by, NEW.actor_type, NEW.reason,
                 NEW.restored_from_id, NEW.created_at)
             IS DISTINCT FROM
             ROW(OLD.id, OLD.article_id, OLD.revision_number, OLD.storage_key,
                 OLD.document_hash, OLD.created_by, OLD.actor_type, OLD.reason,
                 OLD.restored_from_id, OLD.created_at) THEN
            RAISE EXCEPTION 'draft revision snapshot fields are immutable';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_protect_draft_revision_snapshot
        BEFORE UPDATE ON article_draft_revisions
        FOR EACH ROW EXECUTE FUNCTION protect_draft_revision_snapshot();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_protect_formal_article_version ON article_versions")
    op.execute("DROP FUNCTION IF EXISTS protect_formal_article_version()")
    op.execute("DROP TRIGGER IF EXISTS trg_protect_draft_revision_snapshot ON article_draft_revisions")
    op.execute("DROP FUNCTION IF EXISTS protect_draft_revision_snapshot()")
    op.drop_table("draft_command_receipts")
    op.drop_index("ix_article_versions_source_draft_revision_id", table_name="article_versions")
    op.drop_column("article_versions", "abstract_snapshot")
    op.drop_column("article_versions", "title_snapshot")
    op.drop_column("article_versions", "document_hash")
    op.drop_column("article_versions", "source_draft_revision_id")

    version_status = sa.Enum(
        "draft", "submitted", "under_review", "accepted", "rejected", "published",
        name="versionstatus", native_enum=False,
    )
    compile_status = sa.Enum(
        "pending", "processing", "success", "failed", name="compilestatus", native_enum=False
    )
    op.add_column("article_versions", sa.Column("status", version_status, nullable=False, server_default="draft"))
    op.add_column("article_versions", sa.Column("compile_status", compile_status, nullable=False, server_default="pending"))
    op.add_column("article_versions", sa.Column("active_compile_id", sa.Uuid(), nullable=True))
    op.add_column("article_versions", sa.Column("active_compile_session_id", sa.Uuid(), nullable=True))
    op.add_column("article_versions", sa.Column("active_compile_session_revision", sa.Integer(), nullable=True))
    op.add_column("article_versions", sa.Column("compiled_document_hash", sa.String(length=64), nullable=True))
    op.add_column("article_versions", sa.Column("compiled_session_id", sa.Uuid(), nullable=True))
    op.add_column("article_versions", sa.Column("compiled_session_revision", sa.Integer(), nullable=True))
    op.add_column("article_versions", sa.Column("compile_error_code", sa.String(length=100), nullable=True))
    op.add_column("article_versions", sa.Column("compile_error_message", sa.Text(), nullable=True))
    op.execute("ALTER TABLE article_versions ADD COLUMN IF NOT EXISTS change_summary TEXT")
    op.create_check_constraint(
        "ck_article_versions_active_compile_session_revision_nonnegative",
        "article_versions",
        "active_compile_session_revision IS NULL OR active_compile_session_revision >= 0",
    )
    op.create_check_constraint(
        "ck_article_versions_compiled_session_revision_nonnegative",
        "article_versions",
        "compiled_session_revision IS NULL OR compiled_session_revision >= 0",
    )
    op.create_index("ix_article_versions_status", "article_versions", ["status"])

    op.drop_index("ix_articles_current_draft_revision_id", table_name="articles")
    op.drop_constraint("fk_articles_current_draft_revision", "articles", type_="foreignkey")
    op.drop_column("articles", "current_draft_revision_id")
    op.drop_table("article_draft_revisions")
    op.drop_index("ix_articles_status", table_name="articles")
    op.drop_constraint("ck_articles_draft_revision_number_nonnegative", "articles", type_="check")
    op.drop_column("articles", "draft_revision_number")
    op.drop_column("articles", "status")

    op.create_table(
        "article_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("article_version_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_saved_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["article_version_id"], ["article_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", name="uq_article_sessions_article"),
    )
    op.create_index("ix_article_sessions_article_id", "article_sessions", ["article_id"])
    op.create_index("ix_article_sessions_article_version_id", "article_sessions", ["article_version_id"])
