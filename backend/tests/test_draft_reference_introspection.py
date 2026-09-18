import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleDraftRevision,
    ArticleVersion,
    DraftCommandReceipt,
)
from app.models.base import Base
from app.models.user import User
from app.services import article_service, draft_reference_service


@pytest.fixture()
def db_and_storage():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            Article.__table__,
            ArticleAuthor.__table__,
            ArticleDraftRevision.__table__,
            ArticleVersion.__table__,
            DraftCommandReceipt.__table__,
        ],
    )
    db = Session(engine)
    user = User(
        id=uuid.uuid4(),
        clerk_id="reference-user",
        email="reference@example.com",
        full_name="Reference User",
        affiliation=None,
        bio=None,
    )
    db.add(user)
    db.commit()
    objects: dict[str, object] = {}

    def put(key, value):
        if key in objects:
            raise HTTPException(status_code=409, detail="exists")
        objects[key] = value

    with (
        patch("app.core.s3.put_json_key_immutable", side_effect=put),
        patch("app.core.s3.get_json_key", side_effect=lambda key: objects.get(key)),
        patch("app.core.s3.delete_key", side_effect=lambda key: objects.pop(key, None)),
        patch(
            "app.services.butex_worker_client.normalize_document",
            side_effect=lambda value: value,
        ),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
    ):
        yield db, user, objects
    db.close()


def actor(user: User) -> Actor:
    return Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method="agent",
        scopes=frozenset({"articles:read"}),
    )


def test_reference_catalog_reads_canonical_snapshot_without_revision_side_effects(
    db_and_storage,
):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    revision_id = article.current_draft_revision_id
    revision_count = len(db.scalars(select(ArticleDraftRevision)).all())
    storage_keys = set(objects)
    canonical_document = next(iter(objects.values()))
    references = [
        {
            "key": "smith2026",
            "authors": "A. Smith",
            "title": "Example paper",
            "year": "2026",
            "venue": "Example Journal",
            "url": "https://example.org/paper",
            "field_separator": "،",
        }
    ]

    with patch(
        "app.services.butex_worker_client.reference_document",
        return_value=references,
    ) as worker:
        result = draft_reference_service.get_references(db, article.id, actor(user))

    worker.assert_called_once_with(canonical_document)
    assert result == {
        "revision_id": revision_id,
        "revision_number": 1,
        "references": references,
    }
    db.refresh(article)
    assert article.current_draft_revision_id == revision_id
    assert article.draft_revision_number == 1
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == revision_count
    assert set(objects) == storage_keys


def test_reference_index_passes_through_stable_ids_and_unresolved_keys_without_write(
    db_and_storage,
):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    revision_id = article.current_draft_revision_id
    canonical_document = next(iter(objects.values()))
    reference_index = {
        "citations": [
            {
                "kind": "cite",
                "block_id": "block-4",
                "field_id": "field-4",
                "token_id": "token-cite-1",
                "keys": ["smith2026", "missing-paper"],
                "unresolved_keys": ["missing-paper"],
            }
        ],
        "cross_references": [
            {
                "kind": "ref",
                "ref_command": "ref",
                "block_id": "block-5",
                "field_id": "field-5",
                "token_id": "token-ref-1",
                "keys": ["fig:overview"],
                "unresolved_keys": [],
            },
            {
                "kind": "ref",
                "ref_command": "eqref",
                "block_id": "block-6",
                "field_id": "field-6",
                "token_id": "token-ref-2",
                "keys": ["eq:missing"],
                "unresolved_keys": ["eq:missing"],
            },
        ],
        "labels": [
            {
                "key": "fig:overview",
                "kind": "fig",
                "caption": "Overview",
                "number": 1,
                "block_id": "figure-1",
            },
            {
                "key": "tab:data",
                "kind": "tab",
                "caption": "Data",
                "number": 1,
                "block_id": "table-1",
            },
            {
                "key": "eq:energy",
                "kind": "eq",
                "caption": "",
                "number": 1,
                "block_id": "block-3",
                "field_id": "field-3",
                "token_id": "token-math-1",
            },
        ],
        "unresolved": {
            "citation_keys": ["missing-paper"],
            "cross_reference_keys": ["eq:missing"],
        },
    }
    revision_count = len(db.scalars(select(ArticleDraftRevision)).all())
    storage_keys = set(objects)

    with patch(
        "app.services.butex_worker_client.reference_index_document",
        return_value=reference_index,
    ) as worker:
        result = draft_reference_service.get_reference_index(
            db, article.id, actor(user)
        )

    worker.assert_called_once_with(canonical_document)
    assert result["revision_id"] == revision_id
    assert result["revision_number"] == 1
    assert result["reference_index"] == reference_index
    db.refresh(article)
    assert article.current_draft_revision_id == revision_id
    assert article.draft_revision_number == 1
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == revision_count
    assert set(objects) == storage_keys
