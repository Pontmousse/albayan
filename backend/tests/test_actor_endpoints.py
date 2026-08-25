from __future__ import annotations

import inspect
import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.core.actor import Actor, ActorDep
from app.core.clerk import AuthDep
from app.models.article import Article, ArticleVersion
from app.models.enums import VersionStatus
from app.models.user import User
from app.routers import articles, editor, reviews, users


class ActorEndpointTests(unittest.TestCase):
    def _user(self, user_id: uuid.UUID) -> User:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        return User(
            id=user_id,
            clerk_id="user_test",
            email="test@example.com",
            full_name="Test User",
            affiliation="Al-Bayan",
            bio=None,
            created_at=now,
            updated_at=now,
        )

    def test_users_me_uses_actor_dependency(self) -> None:
        annotation = inspect.signature(users.read_current_user).parameters[
            "actor"
        ].annotation

        self.assertEqual(annotation, ActorDep)

    def test_users_me_succeeds_for_human_actor(self) -> None:
        user_id = uuid.uuid4()
        db = MagicMock()
        db.get.return_value = self._user(user_id)
        actor = Actor(user_id=user_id, clerk_id="user_test", auth_method="human")

        response = users.read_current_user(actor, db)

        self.assertEqual(response.id, user_id)

    def test_users_me_succeeds_for_agent_actor(self) -> None:
        user_id = uuid.uuid4()
        db = MagicMock()
        db.get.return_value = self._user(user_id)
        actor = Actor(user_id=user_id, clerk_id="user_test", auth_method="agent")

        response = users.read_current_user(actor, db)

        self.assertEqual(response.id, user_id)

    def test_articles_me_uses_actor_dependency(self) -> None:
        annotation = inspect.signature(articles.list_my_articles).parameters[
            "actor"
        ].annotation

        self.assertEqual(annotation, ActorDep)

    def test_articles_me_succeeds_for_human_actor(self) -> None:
        user_id = uuid.uuid4()
        article_id = uuid.uuid4()
        now = datetime(2026, 1, 1, tzinfo=UTC)
        article = Article(id=article_id, title="عنوان", abstract=None, updated_at=now)
        version = ArticleVersion(
            article_id=article_id,
            version_number=1,
            status=VersionStatus.DRAFT,
            submitted_at=None,
        )
        db = MagicMock()
        actor = Actor(user_id=user_id, clerk_id="user_test", auth_method="human")

        with patch(
            "app.routers.articles.article_service.list_articles_for_author",
            return_value=[(article, version)],
        ) as list_mock:
            response = articles.list_my_articles(actor, db)

        self.assertEqual(response[0].id, article_id)
        list_mock.assert_called_once_with(db, user_id)

    def test_articles_me_succeeds_for_agent_actor_and_uses_agent_user_id(self) -> None:
        user_id = uuid.uuid4()
        db = MagicMock()
        actor = Actor(user_id=user_id, clerk_id="user_test", auth_method="agent")

        with patch(
            "app.routers.articles.article_service.list_articles_for_author",
            return_value=[],
        ) as list_mock:
            response = articles.list_my_articles(actor, db)

        self.assertEqual(response, [])
        list_mock.assert_called_once_with(db, user_id)

    def test_submit_article_remains_human_only(self) -> None:
        annotation = inspect.signature(articles.submit_article).parameters[
            "auth"
        ].annotation

        self.assertEqual(annotation, AuthDep)

    def test_submit_review_remains_human_only(self) -> None:
        annotation = inspect.signature(reviews.submit_review).parameters[
            "auth"
        ].annotation

        self.assertEqual(annotation, AuthDep)

    def test_editor_decision_remains_human_only(self) -> None:
        annotation = inspect.signature(editor.editor_decision).parameters[
            "auth"
        ].annotation

        self.assertEqual(annotation, AuthDep)


if __name__ == "__main__":
    unittest.main()
