"""Read-only draft equation inventory built from the authoritative revision."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.services import (
    article_draft_service,
    equation_mapping_service,
    equation_projection_service,
)


def get_equations(
    db: Session,
    article_id: uuid.UUID,
    actor: Actor,
) -> dict:
    article = article_draft_service.assert_editable_author(db, article_id, actor)
    revision = article_draft_service.get_current_revision(db, article)
    document = article_draft_service.read_document(revision)
    mappings = equation_mapping_service.get_equation_mappings(article)

    return {
        "revision_id": revision.id,
        "revision_number": revision.revision_number,
        "document_language": "ar",
        "equation_representation": "canonical_english_latex",
        "variable_mappings": mappings,
        "equations": equation_projection_service.project_document_equations(
            document,
            mappings,
        ),
    }
