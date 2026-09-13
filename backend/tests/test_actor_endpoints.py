from __future__ import annotations

import inspect
import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.core.actor import Actor, ActorDep
from app.core.clerk import AuthDep
from app.models.article import Article, ArticleAuthor, ArticleVersion
from app.models.enums import VersionStatus
from app.models.user import User
from app.routers import articles, editor, reviews, users
from app.schemas.article import ArticleCreate
from app.services import article_service


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

    def test_draft_article_lifecycle_endpoints_use_actor_dependency(self) -> None:
        for endpoint in (
            articles.create_article,
            articles.get_article,
            articles.update_article,
        ):
            with self.subTest(endpoint=endpoint.__name__):
                annotation = inspect.signature(endpoint).parameters["actor"].annotation
                self.assertEqual(annotation, ActorDep)

    def test_agent_can_create_article_using_authenticated_user_id(self) -> None:
        user_id = uuid.uuid4()
        actor = Actor(
            user_id=user_id,
            clerk_id="agent_test",
            auth_method="agent",
        )
        article = Article(id=uuid.uuid4(), submitted_by=user_id, title="عنوان")
        expected = MagicMock()

        with patch.object(
            articles.article_service,
            "create_article",
            return_value=article,
        ) as create, patch.object(
            articles,
            "_detail",
            return_value=expected,
        ):
            result = articles.create_article(
                ArticleCreate(title="عنوان", abstract="ملخص"),
                actor,
                MagicMock(),
            )

        self.assertIs(result, expected)
        create.assert_called_once()
        self.assertEqual(create.call_args.args[1:], (user_id, "عنوان", "ملخص"))

    def test_create_service_links_creator_as_corresponding_author(self) -> None:
        user_id = uuid.uuid4()
        article_id = uuid.uuid4()
        db = MagicMock()
        added: list[object] = []
        db.add.side_effect = added.append

        def assign_article_id() -> None:
            created_article = next(item for item in added if isinstance(item, Article))
            created_article.id = article_id

        db.flush.side_effect = assign_article_id

        created = article_service.create_article(
            db,
            user_id,
            "عنوان",
            "ملخص",
        )

        author_link = next(item for item in added if isinstance(item, ArticleAuthor))
        self.assertEqual(created.submitted_by, user_id)
        self.assertEqual(author_link.article_id, article_id)
        self.assertEqual(author_link.user_id, user_id)
        self.assertEqual(author_link.author_order, 1)
        self.assertTrue(author_link.is_corresponding)
        db.commit.assert_called_once_with()

    def test_submit_article_remains_human_only(self) -> None:
        annotation = inspect.signature(articles.submit_article).parameters[
            "auth"
        ].annotation

        self.assertEqual(annotation, AuthDep)

    def test_delete_article_remains_human_only(self) -> None:
        annotation = inspect.signature(articles.delete_article).parameters[
            "auth"
        ].annotation

        self.assertEqual(annotation, AuthDep)

    def test_article_session_endpoints_use_actor_dependency(self) -> None:
        endpoints = (
            articles.get_article_session,
            articles.update_article_session,
            articles.get_article_session_outline,
            articles.get_article_session_blocks,
            articles.apply_article_session_command,
            articles.save_article_session,
            articles.discard_article_session,
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint.__name__):
                annotation = inspect.signature(endpoint).parameters["actor"].annotation
                self.assertEqual(annotation, ActorDep)

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
