"""add immutable draft history and restore metadata

Revision ID: 017_draft_history
Revises: 016_draft_revisions
Create Date: 2026-09-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_draft_history"
down_revision: Union[str, None] = "016_draft_revisions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_revision_trigger(*, include_history_fields: bool) -> None:
    history_new = ""
    history_old = ""
    if include_history_fields:
        history_new = ", NEW.restored_from_revision_number, NEW.referenced_asset_ids"
        history_old = ", OLD.restored_from_revision_number, OLD.referenced_asset_ids"
    op.execute(
        f"""
        CREATE FUNCTION protect_draft_revision_snapshot() RETURNS trigger AS $$
        BEGIN
          IF ROW(NEW.id, NEW.article_id, NEW.revision_number, NEW.storage_key,
                 NEW.document_hash, NEW.created_by, NEW.actor_type, NEW.reason,
                 NEW.restored_from_id, NEW.created_at{history_new})
             IS DISTINCT FROM
             ROW(OLD.id, OLD.article_id, OLD.revision_number, OLD.storage_key,
                 OLD.document_hash, OLD.created_by, OLD.actor_type, OLD.reason,
                 OLD.restored_from_id, OLD.created_at{history_old}) THEN
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


def upgrade() -> None:
    op.add_column(
        "article_draft_revisions",
        sa.Column("restored_from_revision_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "article_draft_revisions",
        sa.Column(
            "referenced_asset_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_draft_revision_restored_number_positive",
        "article_draft_revisions",
        "restored_from_revision_number IS NULL OR restored_from_revision_number >= 1",
    )
    op.create_check_constraint(
        "ck_draft_revision_asset_ids_array",
        "article_draft_revisions",
        "referenced_asset_ids IS NULL OR jsonb_typeof(referenced_asset_ids) = 'array'",
    )
    op.execute(
        "DROP TRIGGER trg_protect_draft_revision_snapshot ON article_draft_revisions"
    )
    op.execute("DROP FUNCTION protect_draft_revision_snapshot()")
    _create_revision_trigger(include_history_fields=True)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_protect_draft_revision_snapshot ON article_draft_revisions"
    )
    op.execute("DROP FUNCTION protect_draft_revision_snapshot()")
    op.drop_constraint(
        "ck_draft_revision_asset_ids_array",
        "article_draft_revisions",
        type_="check",
    )
    op.drop_constraint(
        "ck_draft_revision_restored_number_positive",
        "article_draft_revisions",
        type_="check",
    )
    op.drop_column("article_draft_revisions", "referenced_asset_ids")
    op.drop_column("article_draft_revisions", "restored_from_revision_number")
    _create_revision_trigger(include_history_fields=False)
