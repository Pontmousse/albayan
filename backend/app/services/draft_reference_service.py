"""Read-only draft reference introspection backed by the private BuTeX worker."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.services import article_draft_service, butex_worker_client


def get_references(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> dict[str, Any]:
    draft = article_draft_service.get_draft(db, article_id, actor)
    return {
        "revision_id": draft["revision_id"],
        "revision_number": draft["revision_number"],
        "references": butex_worker_client.reference_document(draft["document"]),
    }


def get_reference_index(
    db: Session, article_id: uuid.UUID, actor: Actor
) -> dict[str, Any]:
    draft = article_draft_service.get_draft(db, article_id, actor)
    return {
        "revision_id": draft["revision_id"],
        "revision_number": draft["revision_number"],
        "reference_index": butex_worker_client.reference_index_document(
            draft["document"]
        ),
    }
