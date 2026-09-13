from __future__ import annotations

import unittest
import uuid
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.actor import Actor
from app.models.article import Article, ArticleSession, ArticleVersion
from app.models.enums import VersionStatus
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services import article_service, article_session_service


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
            ArticleUpdate(abstract="م" * 5001)

    def test_accepts_partial_updates_and_rejects_empty_or_author_fields(self) -> None:
        self.assertEqual(ArticleUpdate(abstract="ملخص").abstract, "ملخص")
        for payload in ({}, {"title": None}, {"authors": "اسم"}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ArticleUpdate(**payload)

    def test_create_rejects_author_fields_and_trims_metadata(self) -> None:
        payload = ArticleCreate(title="  عنوان  ", abstract="  ملخص  ")
        self.assertEqual(payload.title, "عنوان")
        self.assertEqual(payload.abstract, "ملخص")
        with self.assertRaises(ValidationError):
            ArticleCreate(title="عنوان", authors=["user-2"])


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
        self.version = ArticleVersion(
            id=uuid.uuid4(),
            article_id=self.article.id,
            storage_prefix="articles/test/versions/v1/",
            status=VersionStatus.DRAFT,
        )
        self.actor = Actor(
            user_id=uuid.uuid4(),
            clerk_id="agent_test",
            auth_method="agent",
        )
        self.db = MagicMock()

    def test_updates_database_when_no_active_session_exists(self) -> None:
        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=None,
        ), patch.object(
            article_session_service,
            "_lock_metadata_rows",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service.butex_worker_client,
            "apply_document_command",
        ) as apply_command, patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at:
            updated = article_session_service.update_article_metadata(
                self.db,
                self.article.id,
                self.actor,
                ArticleUpdate(title="عنوان جديد"),
            )

        self.assertIs(updated, self.article)
        self.assertEqual(updated.title, "عنوان جديد")
        self.assertEqual(updated.abstract, "ملخص قديم")
        self.assertIsNotNone(updated.updated_at)
        self.db.commit.assert_called_once_with()
        self.db.refresh.assert_called_once_with(self.article)
        apply_command.assert_not_called()
        put_json_at.assert_not_called()

    def test_updates_active_session_and_increments_revision(self) -> None:
        session = ArticleSession(
            id=uuid.uuid4(),
            article_id=self.article.id,
            article_version_id=self.version.id,
            revision=4,
            last_saved_revision=2,
            created_by=self.actor.user_id,
            updated_by=self.actor.user_id,
        )
        current = {
            "node_type": "DocumentObject",
            "meta": {"title": "قديم", "abstract": "ملخص قديم"},
            "blocks": [],
        }
        synchronized = {
            "node_type": "DocumentObject",
            "meta": {"title": "جديد", "abstract": "ملخص جديد"},
            "blocks": [],
        }

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service,
            "_lock_metadata_rows",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "_session_document",
            return_value=current,
        ), patch.object(
            article_session_service,
            "_synchronize_document_metadata",
            return_value=synchronized,
        ) as synchronize, patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at, patch.object(
            article_session_service,
            "_write_meta",
        ) as write_meta:
            updated = article_session_service.update_article_metadata(
                self.db,
                self.article.id,
                self.actor,
                ArticleUpdate(title="جديد", abstract="ملخص جديد"),
            )

        self.assertEqual(updated.title, "جديد")
        self.assertEqual(updated.abstract, "ملخص جديد")
        self.assertEqual(
            article_service.document_metadata_mismatches(updated, synchronized),
            [],
        )
        self.assertEqual(session.revision, 5)
        self.assertEqual(session.last_saved_revision, 2)
        synchronize.assert_called_once_with(
            current,
            title="جديد",
            abstract="ملخص جديد",
        )
        put_json_at.assert_called_once_with(
            article_session_service.session_storage_prefix(self.article.id),
            article_session_service.SESSION_DOCUMENT,
            synchronized,
        )
        write_meta.assert_called_once_with(self.article.id, session)
        self.db.commit.assert_called_once_with()

    def test_metadata_noop_does_not_increment_session_revision(self) -> None:
        session = ArticleSession(
            id=uuid.uuid4(),
            article_id=self.article.id,
            article_version_id=self.version.id,
            revision=4,
            last_saved_revision=2,
            created_by=self.actor.user_id,
            updated_by=self.actor.user_id,
        )
        current = {
            "node_type": "DocumentObject",
            "meta": {"title": "قديم", "abstract": "ملخص قديم"},
            "blocks": [],
        }

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service,
            "_lock_metadata_rows",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "_session_document",
            return_value=current,
        ), patch.object(
            article_session_service,
            "_synchronize_document_metadata",
            return_value=current,
        ), patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at, patch.object(
            article_session_service,
            "_write_meta",
        ) as write_meta:
            article_session_service.update_article_metadata(
                self.db,
                self.article.id,
                self.actor,
                ArticleUpdate(title="قديم"),
            )

        self.assertEqual(session.revision, 4)
        put_json_at.assert_not_called()
        write_meta.assert_not_called()

    def test_synchronized_session_is_the_document_saved_to_draft(self) -> None:
        self.article.title = "جديد"
        self.article.abstract = "ملخص جديد"
        session = ArticleSession(
            id=uuid.uuid4(),
            article_id=self.article.id,
            article_version_id=self.version.id,
            revision=2,
            last_saved_revision=0,
            created_by=self.actor.user_id,
            updated_by=self.actor.user_id,
        )
        synchronized = {
            "node_type": "DocumentObject",
            "meta": {"title": "جديد", "abstract": "ملخص جديد"},
            "blocks": [],
        }

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(self.article, self.version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, synchronized),
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service.s3,
            "put_json",
        ) as put_json, patch.object(
            article_session_service,
            "_write_meta",
        ), patch.object(
            article_session_service.compile_service,
            "hash_document",
            return_value="hash",
        ):
            article_session_service.save_session_to_draft(
                self.db,
                self.article.id,
                self.actor,
            )

        put_json.assert_called_once_with(self.version.storage_prefix, synchronized)
        self.assertEqual(session.last_saved_revision, 2)
        self.assertEqual(
            article_service.document_metadata_mismatches(
                self.article,
                synchronized,
            ),
            [],
        )

    def test_rejects_submitted_and_other_frozen_versions(self) -> None:
        for status in (VersionStatus.SUBMITTED, VersionStatus.UNDER_REVIEW):
            self.version.status = status
            with self.subTest(status=status), patch.object(
                article_service,
                "current_version",
                return_value=self.version,
            ), patch.object(
                article_service,
                "assert_is_author",
                return_value=self.article,
            ), self.assertRaises(HTTPException) as raised:
                article_session_service.update_article_metadata(
                    self.db,
                    self.article.id,
                    self.actor,
                    ArticleUpdate(title="عنوان جديد"),
                )

            self.assertEqual(raised.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_metadata_update_rejects_non_author_without_touching_session(self) -> None:
        not_found = HTTPException(status_code=404, detail="المقال غير موجود.")
        with patch.object(
            article_service,
            "assert_is_author",
            side_effect=not_found,
        ), patch.object(
            article_session_service,
            "_lock_current_session",
        ) as lock_session, self.assertRaises(HTTPException) as raised:
            article_session_service.update_article_metadata(
                self.db,
                self.article.id,
                self.actor,
                ArticleUpdate(abstract="جديد"),
            )

        self.assertEqual(raised.exception.status_code, 404)
        lock_session.assert_not_called()
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
