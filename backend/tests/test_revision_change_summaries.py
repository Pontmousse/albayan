import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import Article, ArticleAuthor, ArticleDraftRevision, ArticleVersion
from app.models.base import Base
from app.models.revision_summary import DraftRevisionChangeSummary
from app.models.user import User
from app.services import article_draft_service, article_service, revision_summary_service


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
            DraftRevisionChangeSummary.__table__,
        ],
    )
    db = Session(engine)
    user = User(
        id=uuid.uuid4(),
        clerk_id="summary-user",
        email="summary@example.com",
        full_name="Summary User",
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
        yield db, user
    db.close()


def actor(user: User) -> Actor:
    return Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method="human",
        scopes=frozenset({"articles:read", "articles:draft:write"}),
    )


def _second_revision(db: Session, user: User):
    article = article_service.create_article(db, user.id, "الأول", None)
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db,
        article.id,
        actor(user),
        1,
        {
            **draft["document"],
            "meta": {"title": "الثاني", "abstract": ""},
        },
    )
    db.refresh(article)
    return article, db.get(ArticleDraftRevision, article.current_draft_revision_id)


def test_first_revision_returns_null_without_worker_or_llm(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    with patch("app.services.butex_worker_client.diff_documents") as diff, patch(
        "app.services.openrouter_client.summarize_revision_diff"
    ) as summarize:
        result = revision_summary_service.get_revision_change_summary(
            db, article.id, article.current_draft_revision_id, actor(user)
        )
    assert result == {"summary": None}
    diff.assert_not_called()
    summarize.assert_not_called()


def test_valid_summary_is_cached_and_reused(db_and_storage) -> None:
    db, user = db_and_storage
    article, revision = _second_revision(db, user)
    diff_payload = {
        "version": 1,
        "changed": True,
        "truncated": False,
        "chunks": [{"kind": "added", "text": "new title"}],
    }
    summary = {
        "version": 1,
        "items": [{"kind": "edited", "text": "عُدّل عنوان المقال."}],
    }
    with patch(
        "app.services.butex_worker_client.diff_documents", return_value=diff_payload
    ) as diff, patch(
        "app.services.openrouter_client.summarize_revision_diff", return_value=summary
    ) as summarize:
        first = revision_summary_service.get_revision_change_summary(
            db, article.id, revision.id, actor(user)
        )
    assert first == {"summary": summary}
    diff.assert_called_once()
    summarize.assert_called_once_with(diff_payload)
    cached = db.get(DraftRevisionChangeSummary, revision.id)
    assert cached is not None
    assert cached.schema_version == 1
    assert cached.summary == summary

    with patch("app.services.butex_worker_client.diff_documents") as diff_again, patch(
        "app.services.openrouter_client.summarize_revision_diff"
    ) as summarize_again:
        second = revision_summary_service.get_revision_change_summary(
            db, article.id, revision.id, actor(user)
        )
    assert second == {"summary": summary}
    diff_again.assert_not_called()
    summarize_again.assert_not_called()


def test_unchanged_diff_caches_empty_summary_without_llm(db_and_storage) -> None:
    db, user = db_and_storage
    article, revision = _second_revision(db, user)
    with patch(
        "app.services.butex_worker_client.diff_documents",
        return_value={
            "version": 1,
            "changed": False,
            "truncated": False,
            "chunks": [],
        },
    ), patch("app.services.openrouter_client.summarize_revision_diff") as summarize:
        result = revision_summary_service.get_revision_change_summary(
            db, article.id, revision.id, actor(user)
        )
    assert result == {"summary": {"version": 1, "items": []}}
    summarize.assert_not_called()
    assert db.get(DraftRevisionChangeSummary, revision.id).summary == {
        "version": 1,
        "items": [],
    }


def test_provider_failure_returns_null_without_persisting(db_and_storage) -> None:
    db, user = db_and_storage
    article, revision = _second_revision(db, user)
    with patch(
        "app.services.butex_worker_client.diff_documents",
        return_value={
            "version": 1,
            "changed": True,
            "truncated": False,
            "chunks": [{"kind": "removed", "text": "old"}],
        },
    ), patch(
        "app.services.openrouter_client.summarize_revision_diff", return_value=None
    ):
        result = revision_summary_service.get_revision_change_summary(
            db, article.id, revision.id, actor(user)
        )
    assert result == {"summary": None}
    assert db.get(DraftRevisionChangeSummary, revision.id) is None


def test_butex_unavailable_returns_null(db_and_storage) -> None:
    db, user = db_and_storage
    article, revision = _second_revision(db, user)
    with patch(
        "app.services.butex_worker_client.diff_documents",
        side_effect=HTTPException(status_code=404, detail="route unavailable"),
    ), patch("app.services.openrouter_client.summarize_revision_diff") as summarize:
        result = revision_summary_service.get_revision_change_summary(
            db, article.id, revision.id, actor(user)
        )
    assert result == {"summary": None}
    summarize.assert_not_called()


def test_summary_remains_author_only(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    stranger = User(
        id=uuid.uuid4(),
        clerk_id="summary-stranger",
        email="stranger-summary@example.com",
        full_name="Stranger",
        affiliation=None,
        bio=None,
    )
    db.add(stranger)
    db.commit()

    with pytest.raises(HTTPException) as raised:
        revision_summary_service.get_revision_change_summary(
            db, article.id, article.current_draft_revision_id, actor(stranger)
        )
    assert raised.value.status_code == 404
