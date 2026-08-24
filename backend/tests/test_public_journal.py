from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

from app.models.article import Article, ArticleAuthor, ArticleVersion
from app.models.enums import VersionStatus
from app.models.user import User
from app.services import public_journal_service


class PublicJournalServiceTests(unittest.TestCase):
    def _article(
        self,
        *,
        title: str,
        status: VersionStatus,
        submitted_at: datetime | None = None,
    ) -> Article:
        article_id = uuid.uuid4()
        article = Article(
            id=article_id,
            submitted_by=uuid.uuid4(),
            title=title,
            abstract=f"ملخص {title}",
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        article.versions = [
            ArticleVersion(
                article_id=article_id,
                version_number=1,
                storage_prefix=f"articles/{article_id}/versions/v1/",
                status=status,
                submitted_at=submitted_at,
            )
        ]
        user = User(
            id=uuid.uuid4(),
            clerk_id="clerk_test",
            email="author@example.com",
            full_name="د. أحمد",
        )
        article.author_links = [
            ArticleAuthor(
                article_id=article_id,
                user_id=user.id,
                author_order=1,
                is_corresponding=True,
                user=user,
            )
        ]
        return article

    def test_public_journal_summary_counts_only_published(self) -> None:
        published = self._article(
            title="منشور",
            status=VersionStatus.PUBLISHED,
            submitted_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        draft = self._article(title="مسودة", status=VersionStatus.DRAFT)
        db = Mock()
        db.scalars.return_value.unique.return_value.all.return_value = [
            draft,
            published,
        ]

        count, articles = public_journal_service.public_journal_summary(db)

        self.assertEqual(count, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "منشور")
        self.assertEqual(articles[0].authors[0].full_name, "د. أحمد")


if __name__ == "__main__":
    unittest.main()
