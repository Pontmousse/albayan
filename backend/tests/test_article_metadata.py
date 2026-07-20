from __future__ import annotations

import unittest
import uuid
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.article import Article, ArticleVersion
from app.models.enums import VersionStatus
from app.schemas.article import ArticleUpdate
from app.services import article_service


class ArticleUpdateSchemaTests(unittest.TestCase):
    def test_trims_title_and_abstract(self) -> None:
        payload = ArticleUpdate(title="  عنوان  ", abstract="\n ملخص \n")
        self.assertEqual(payload.title, "عنوان")
        self.assertEqual(payload.abstract, "ملخص")

    def test_rejects_blank_or_long_title(self) -> None:
        for title in ("   ", "أ" * 501):
            with self.subTest(length=len(title)), self.assertRaises(ValidationError):
                ArticleUpdate(title=title)

    def test_rejects_long_abstract_after_trimming(self) -> None:
        with self.assertRaises(ValidationError):
            ArticleUpdate(title="عنوان", abstract="م" * 5001)


class DocumentMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.article = Article(title="عنوان المقال", abstract="ملخص المقال")
        self.version = ArticleVersion(storage_prefix="articles/test/versions/v1/")

    def test_matches_while_ignoring_surrounding_whitespace(self) -> None:
        document = {
            "meta": {
                "title": "\n  عنوان المقال  \n",
                "abstract": "\n\n ملخص المقال \n",
            }
        }
        self.assertEqual(
            article_service.document_metadata_mismatches(self.article, document),
            [],
        )

    def test_null_and_empty_abstract_match(self) -> None:
        self.article.abstract = None
        document = {"meta": {"title": "عنوان المقال", "abstract": "  "}}
        self.assertEqual(
            article_service.document_metadata_mismatches(self.article, document),
            [],
        )

    def test_reports_each_mismatch_and_missing_meta(self) -> None:
        cases = (
            ({"meta": {"title": "مختلف", "abstract": "ملخص المقال"}}, ["title"]),
            ({"meta": {"title": "عنوان المقال", "abstract": "مختلف"}}, ["abstract"]),
            ({"meta": {"title": "مختلف", "abstract": "مختلف"}}, ["title", "abstract"]),
            ({"blocks": []}, ["title", "abstract"]),
        )
        for document, expected in cases:
            with self.subTest(document=document):
                self.assertEqual(
                    article_service.document_metadata_mismatches(
                        self.article, document
                    ),
                    expected,
                )

    def test_assertion_returns_arabic_409_for_different_fields(self) -> None:
        documents = (
            {"meta": {"title": "مختلف", "abstract": "ملخص المقال"}},
            {"meta": {"title": "عنوان المقال", "abstract": "مختلف"}},
            {"meta": {"title": "مختلف", "abstract": "مختلف"}},
        )
        for document in documents:
            with self.subTest(document=document), patch.object(
                article_service.s3, "get_json", return_value=document
            ), self.assertRaises(HTTPException) as raised:
                article_service.assert_document_metadata_matches(
                    self.article, self.version
                )
            self.assertEqual(raised.exception.status_code, 409)
            self.assertIn("داخل المحرر", str(raised.exception.detail))
            self.assertIn("يدويًا", str(raised.exception.detail))


class DraftMetadataUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.article = Article(
            id=uuid.uuid4(), title="قديم", abstract="ملخص قديم"
        )
        self.version = ArticleVersion(status=VersionStatus.DRAFT)
        self.db = Mock()

    def test_updates_database_fields_without_touching_document(self) -> None:
        with patch.object(
            article_service, "current_version", return_value=self.version
        ), patch.object(article_service.s3, "get_json") as get_json, patch.object(
            article_service.s3, "put_json"
        ) as put_json:
            updated = article_service.update_draft_metadata(
                self.db, self.article, "عنوان جديد", None
            )

        self.assertIs(updated, self.article)
        self.assertEqual(updated.title, "عنوان جديد")
        self.assertIsNone(updated.abstract)
        self.assertIsNotNone(updated.updated_at)
        self.db.commit.assert_called_once_with()
        self.db.refresh.assert_called_once_with(self.article)
        get_json.assert_not_called()
        put_json.assert_not_called()

    def test_rejects_submitted_article(self) -> None:
        self.version.status = VersionStatus.SUBMITTED
        with patch.object(
            article_service, "current_version", return_value=self.version
        ), self.assertRaises(HTTPException) as raised:
            article_service.update_draft_metadata(
                self.db, self.article, "عنوان جديد", "ملخص"
            )

        self.assertEqual(raised.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_non_author_is_hidden_as_not_found(self) -> None:
        self.db.get.return_value = self.article
        self.db.scalar.return_value = None
        with self.assertRaises(HTTPException) as raised:
            article_service.assert_is_author(
                self.db, self.article.id, uuid.uuid4()
            )
        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
