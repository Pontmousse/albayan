"""PostgreSQL-only checks for locking and database immutability guarantees."""

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.core.actor import Actor
from app.models.article import Article, ArticleDraftRevision, ArticleVersion
from app.models.enums import DraftRevisionReason, SourceType
from app.models.user import User
from app.services import article_draft_service, article_service


DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not DATABASE_URL.startswith("postgresql"),
    reason="TEST_DATABASE_URL must point to disposable PostgreSQL",
)


@pytest.fixture()
def postgres_article():
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    storage: dict[str, object] = {}
    with Session(engine) as db:
        user = User(
            id=uuid.uuid4(),
            clerk_id=f"draft-pg-{uuid.uuid4()}",
            email=f"draft-pg-{uuid.uuid4()}@example.com",
            full_name="Draft PostgreSQL",
            affiliation=None,
            bio=None,
        )
        db.add(user)
        db.commit()
        user_id = user.id

    def put(key, value):
        if key in storage:
            raise HTTPException(status_code=409, detail="exists")
        storage[key] = value

    patches = (
        patch("app.core.s3.put_json_key_immutable", side_effect=put),
        patch("app.core.s3.get_json_key", side_effect=lambda key: storage.get(key)),
        patch("app.core.s3.delete_key", side_effect=lambda key: storage.pop(key, None)),
        patch("app.services.butex_worker_client.normalize_document", side_effect=lambda value: value),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
    )
    for active_patch in patches:
        active_patch.start()
    try:
        with sessions() as db:
            article = article_service.create_article(db, user_id, "عنوان", None)
            article_id = article.id
        yield sessions, user_id, article_id
    finally:
        for active_patch in reversed(patches):
            active_patch.stop()
        with sessions() as db:
            article = db.get(Article, article_id)
            if article is not None:
                db.delete(article)
                db.commit()
            user = db.get(User, user_id)
            if user is not None:
                db.delete(user)
                db.commit()
        engine.dispose()


def _actor(user_id: uuid.UUID) -> Actor:
    return Actor(
        user_id=user_id,
        clerk_id="draft-pg",
        auth_method="human",
        scopes=frozenset(),
    )


def test_two_sessions_have_exactly_one_revision_winner(postgres_article):
    sessions, user_id, article_id = postgres_article
    ready = threading.Barrier(2)

    def save(block_id: str):
        with sessions() as db:
            article = db.get(Article, article_id)
            assert article is not None
            revision = article_draft_service.get_current_revision(db, article)
            document = article_draft_service.read_document(revision)
            candidate = {**document, "blocks": [{"id": block_id}]}
            ready.wait(timeout=5)
            try:
                result = article_draft_service.put_draft(
                    db, article_id, _actor(user_id), 1, candidate
                )
                return result["revision_number"]
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(save, ("browser", "agent")))

    assert outcomes == [2, 409]
    with sessions() as db:
        article = db.get(Article, article_id)
        assert article is not None and article.draft_revision_number == 2


def test_database_rejects_snapshot_and_formal_version_updates(postgres_article):
    sessions, _, article_id = postgres_article
    with sessions() as db:
        article = db.get(Article, article_id)
        assert article is not None
        revision = article_draft_service.get_current_revision(db, article)
        revision.reason = DraftRevisionReason.AUTOSAVE
        with pytest.raises(DBAPIError):
            db.commit()
        db.rollback()

        revision = db.get(ArticleDraftRevision, revision.id)
        assert revision is not None
        revision.referenced_asset_ids = ["assets/changed.png"]
        with pytest.raises(DBAPIError):
            db.commit()
        db.rollback()

        revision = db.get(ArticleDraftRevision, revision.id)
        assert revision is not None
        revision.restored_from_revision_number = 1
        with pytest.raises(DBAPIError):
            db.commit()
        db.rollback()

        version = ArticleVersion(
            article_id=article_id,
            version_number=1,
            storage_prefix=f"articles/{article_id}/versions/v1",
            source_type=SourceType.WEB_EDITOR,
            source_draft_revision_id=revision.id,
            document_hash=revision.document_hash,
            title_snapshot="عنوان",
            abstract_snapshot=None,
        )
        db.add(version)
        db.commit()
        version.title_snapshot = "عنوان معدل"
        with pytest.raises(DBAPIError):
            db.commit()
        db.rollback()


def test_stale_restore_uses_structured_conflict_across_sessions(postgres_article):
    sessions, user_id, article_id = postgres_article
    actor = _actor(user_id)
    with sessions() as setup:
        article = setup.get(Article, article_id)
        assert article is not None
        target_id = article.current_draft_revision_id
        draft = article_draft_service.get_draft(setup, article_id, actor)
        article_draft_service.put_draft(
            setup,
            article_id,
            actor,
            1,
            {**draft["document"], "blocks": [{"id": "second"}]},
        )

    first = sessions()
    stale = sessions()
    try:
        current = article_draft_service.get_draft(first, article_id, actor)
        article_draft_service.put_draft(
            first,
            article_id,
            actor,
            2,
            {**current["document"], "blocks": [{"id": "third"}]},
        )
        with pytest.raises(HTTPException) as raised:
            article_draft_service.restore_revision(
                stale, article_id, target_id, actor, 2
            )
        assert raised.value.status_code == 409
        assert raised.value.detail == {
            "code": "revision_conflict",
            "message": "وصل تعديل أحدث للمسودة؛ حُمّلت النسخة الأحدث من الخادم.",
            "current_revision": 3,
        }
    finally:
        first.close()
        stale.close()
