import uuid

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import Article, ArticleAuthor, ArticleDraftRevision, ArticleVersion
from app.models.base import Base
from app.models.enums import ArticleStatus
from app.models.user import User
from app.routers.equation_mappings import get_equation_mappings, put_equation_mappings
from app.schemas.equation_mapping import EquationMappingsUpdate


def _database() -> tuple[Session, Article, Actor]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            Article.__table__,
            ArticleDraftRevision.__table__,
            ArticleVersion.__table__,
            ArticleAuthor.__table__,
        ],
    )
    db = Session(engine)
    user = User(
        id=uuid.uuid4(),
        clerk_id="equation-panel-user",
        email="equation-panel@example.com",
        full_name="Equation Panel User",
        gender=None,
        affiliation=None,
        bio=None,
    )
    article = Article(
        id=uuid.uuid4(),
        submitted_by=user.id,
        title="عنوان",
        abstract=None,
        status=ArticleStatus.DRAFT,
        draft_revision_number=7,
        equation_mappings={"x": "س"},
    )
    author = ArticleAuthor(
        article_id=article.id,
        user_id=user.id,
        author_order=1,
        is_corresponding=True,
    )
    db.add_all([user, article, author])
    db.commit()
    return db, article, Actor(user_id=user.id, clerk_id=user.clerk_id, auth_method="human")


def test_author_can_read_current_equation_mappings() -> None:
    db, article, actor = _database()
    try:
        assert get_equation_mappings(article.id, actor, db) == {
            "mappings": {"x": "س"}
        }
    finally:
        db.close()


def test_author_can_replace_or_reset_mappings_without_creating_draft_revision() -> None:
    db, article, actor = _database()
    try:
        current_revision_id = article.current_draft_revision_id
        before_revision_number = article.draft_revision_number

        result = put_equation_mappings(
            article.id,
            EquationMappingsUpdate(mappings={"x": "ص", "y": "ع"}),
            actor,
            db,
        )
        assert result == {"mappings": {"x": "ص", "y": "ع"}}

        db.expire_all()
        reloaded = db.get(Article, article.id)
        assert reloaded is not None
        assert reloaded.equation_mappings == {"x": "ص", "y": "ع"}
        assert reloaded.current_draft_revision_id == current_revision_id
        assert reloaded.draft_revision_number == before_revision_number
        assert db.scalar(select(ArticleDraftRevision).count()) is None

        reset = put_equation_mappings(
            article.id,
            EquationMappingsUpdate(mappings={}),
            actor,
            db,
        )
        assert reset == {"mappings": {}}
    finally:
        db.close()


def test_non_author_cannot_read_or_update_mappings() -> None:
    db, article, _actor = _database()
    stranger = Actor(
        user_id=uuid.uuid4(),
        clerk_id="stranger",
        auth_method="human",
    )
    try:
        with pytest.raises(HTTPException) as read_error:
            get_equation_mappings(article.id, stranger, db)
        assert read_error.value.status_code == 404

        with pytest.raises(HTTPException) as write_error:
            put_equation_mappings(
                article.id,
                EquationMappingsUpdate(mappings={"x": "س"}),
                stranger,
                db,
            )
        assert write_error.value.status_code == 404
    finally:
        db.close()


def test_frozen_article_rejects_mapping_update() -> None:
    db, article, actor = _database()
    try:
        article.status = ArticleStatus.SUBMITTED
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            put_equation_mappings(
                article.id,
                EquationMappingsUpdate(mappings={"x": "ص"}),
                actor,
                db,
            )
        assert exc_info.value.status_code == 409
    finally:
        db.close()


@pytest.mark.parametrize(
    "payload",
    [
        {"mappings": {"": "س"}},
        {"mappings": {"x": ""}},
        {"mappings": {"x": 3}},
        {"mappings": {"x": " ", "y": "ص"}},
        {"mappings": {"x" * 129: "س"}},
        {"mappings": {"x": "س" * 129}},
        {"mappings": []},
    ],
)
def test_mapping_payload_rejects_malformed_values(payload) -> None:
    with pytest.raises(ValidationError):
        EquationMappingsUpdate.model_validate(payload)


def test_mapping_payload_trims_surrounding_whitespace() -> None:
    payload = EquationMappingsUpdate.model_validate(
        {"mappings": {" x ": " س "}}
    )
    assert payload.mappings == {"x": "س"}
