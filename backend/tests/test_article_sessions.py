from __future__ import annotations

import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.core.actor import Actor
from app.models.article import Article, ArticleSession, ArticleVersion
from app.models.enums import VersionStatus
from app.schemas.article import DocumentCommandPayload
from app.services import article_session_service


def _actor() -> Actor:
    return Actor(user_id=uuid.uuid4(), clerk_id="user_test", auth_method="human")


def _article(article_id: uuid.UUID) -> Article:
    return Article(
        id=article_id,
        submitted_by=uuid.uuid4(),
        title="عنوان",
        abstract="ملخص",
    )


def _version(article_id: uuid.UUID) -> ArticleVersion:
    return ArticleVersion(
        id=uuid.uuid4(),
        article_id=article_id,
        version_number=1,
        storage_prefix=f"articles/{article_id}/versions/v1/",
        status=VersionStatus.DRAFT,
    )


def _session(
    article_id: uuid.UUID,
    version_id: uuid.UUID,
    revision: int = 0,
) -> ArticleSession:
    return ArticleSession(
        id=uuid.uuid4(),
        article_id=article_id,
        article_version_id=version_id,
        revision=revision,
        last_saved_revision=0,
        created_by=uuid.uuid4(),
        updated_by=uuid.uuid4(),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class ArticleSessionServiceTests(unittest.TestCase):
    def test_get_or_create_session_normalizes_from_current_draft_document(self) -> None:
        article_id = uuid.uuid4()
        article = _article(article_id)
        version = _version(article_id)
        normalized = {
            "node_type": "DocumentObject",
            "blocks": [{"id": "block_1", "value": "نص"}],
        }
        db = MagicMock()
        db.scalar.return_value = None
        db.refresh.side_effect = lambda obj: setattr(
            obj, "updated_at", datetime(2026, 1, 1, tzinfo=UTC)
        )

        with patch.object(
            article_session_service.article_service,
            "assert_is_author",
            return_value=article,
        ), patch.object(
            article_session_service.article_service,
            "current_version",
            return_value=version,
        ), patch.object(
            article_session_service.s3,
            "get_json",
            return_value={"blocks": [{"value": "نص"}]},
        ), patch.object(
            article_session_service.butex_worker_client,
            "normalize_document",
            return_value=normalized,
        ) as normalize, patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at:
            session, document = article_session_service.get_or_create_session(
                db,
                article_id,
                _actor(),
            )

        self.assertEqual(session.article_id, article_id)
        self.assertEqual(session.article_version_id, version.id)
        self.assertEqual(session.revision, 0)
        self.assertEqual(document, normalized)
        normalize.assert_called_once_with({"blocks": [{"value": "نص"}]})
        written_keys = [call.args[1] for call in put_json_at.call_args_list]
        self.assertIn("session/document.json", written_keys)
        self.assertIn("session/meta.json", written_keys)

    def test_get_or_create_session_reuses_existing_session(self) -> None:
        article_id = uuid.uuid4()
        article = _article(article_id)
        version = _version(article_id)
        session = _session(article_id, version.id, revision=3)
        db = MagicMock()
        db.scalar.return_value = session

        with patch.object(
            article_session_service.article_service,
            "assert_is_author",
            return_value=article,
        ), patch.object(
            article_session_service.article_service,
            "current_version",
            return_value=version,
        ), patch.object(
            article_session_service.s3,
            "get_json_at",
            return_value={"blocks": []},
        ), patch.object(
            article_session_service.butex_worker_client,
            "normalize_document",
        ) as normalize:
            reused, document = article_session_service.get_or_create_session(
                db,
                article_id,
                _actor(),
            )

        self.assertIs(reused, session)
        self.assertEqual(document, {"blocks": []})
        normalize.assert_not_called()

    def test_apply_session_command_increments_revision_and_writes_record(self) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        article = _article(article_id)
        version = _version(article_id)
        session = _session(article_id, version.id)
        before = {"blocks": []}
        after = {"blocks": [{"id": "block_1", "value": "نص"}]}
        command_id = uuid.uuid4()
        payload = DocumentCommandPayload(
            command_id=command_id,
            base_revision=0,
            command={
                "op": "insert_text_block",
                "kind": "paragraph",
                "text": "نص",
                "anchor": {"end": True},
            },
        )

        db = MagicMock()

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(article, version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, before),
        ), patch.object(
            article_session_service,
            "_command_record",
            side_effect=[None, None],
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service.butex_worker_client,
            "apply_document_command",
            return_value=after,
        ), patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at:
            result = article_session_service.apply_session_command(
                db,
                article_id,
                actor,
                payload,
            )

        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["affected_block_ids"], ["block_1"])
        self.assertEqual(session.revision, 1)
        self.assertTrue(
            any(
                call.args[1] == "session/document.json"
                for call in put_json_at.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.args[1] == f"session/commands/{command_id}.json"
                for call in put_json_at.call_args_list
            )
        )
        db.commit.assert_called_once_with()

    def test_apply_session_command_replays_duplicate_command_id(self) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        version = _version(article_id)
        session = _session(article_id, version.id)
        payload = DocumentCommandPayload(
            command_id=uuid.uuid4(),
            base_revision=0,
            command={"op": "remove_block", "block_id": "block_1"},
        )
        response = {
            "ok": True,
            "revision": 1,
            "last_saved_revision": 0,
            "document": {"blocks": []},
            "affected_block_ids": ["block_1"],
        }
        request_hash = article_session_service._request_hash(payload)

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(_article(article_id), version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, {"blocks": []}),
        ), patch.object(
            article_session_service,
            "_command_record",
            return_value={"request_hash": request_hash, "response": response},
        ), patch.object(
            article_session_service.butex_worker_client,
            "apply_document_command",
        ) as worker:
            result = article_session_service.apply_session_command(
                MagicMock(),
                article_id,
                actor,
                payload,
            )

        self.assertEqual(result, response)
        worker.assert_not_called()

    def test_apply_session_command_rejects_reused_command_id_with_new_payload(
        self,
    ) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        version = _version(article_id)
        session = _session(article_id, version.id)
        payload = DocumentCommandPayload(
            command_id=uuid.uuid4(),
            base_revision=0,
            command={"op": "remove_block", "block_id": "block_1"},
        )

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(_article(article_id), version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, {"blocks": []}),
        ), patch.object(
            article_session_service,
            "_command_record",
            return_value={"request_hash": "different"},
        ), patch.object(
            article_session_service.butex_worker_client,
            "apply_document_command",
        ) as worker, self.assertRaises(HTTPException) as raised:
            article_session_service.apply_session_command(
                MagicMock(),
                article_id,
                actor,
                payload,
            )

        self.assertEqual(raised.exception.status_code, 409)
        worker.assert_not_called()

    def test_apply_session_command_rejects_stale_revision(self) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        version = _version(article_id)
        session = _session(article_id, version.id, revision=2)
        payload = DocumentCommandPayload(
            command_id=uuid.uuid4(),
            base_revision=1,
            command={"op": "remove_block", "block_id": "block_1"},
        )

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(_article(article_id), version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, {"blocks": []}),
        ), patch.object(
            article_session_service,
            "_command_record",
            return_value=None,
        ), self.assertRaises(HTTPException) as raised:
            article_session_service.apply_session_command(
                MagicMock(),
                article_id,
                actor,
                payload,
            )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["current_revision"], 2)

    def test_save_session_copies_document_to_current_draft_without_closing(self) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        version = _version(article_id)
        session = _session(article_id, version.id, revision=4)
        document = {"blocks": [{"id": "block_1"}]}
        db = MagicMock()

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(_article(article_id), version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, document),
        ), patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service.s3,
            "put_json",
        ) as put_json, patch.object(
            article_session_service.s3,
            "put_json_at",
        ):
            result = article_session_service.save_session_to_draft(
                db,
                article_id,
                actor,
            )

        put_json.assert_called_once_with(version.storage_prefix, document)
        self.assertEqual(
            result,
            {"ok": True, "revision": 4, "last_saved_revision": 4},
        )
        self.assertEqual(session.last_saved_revision, 4)
        db.delete.assert_not_called()

    def test_update_session_document_normalizes_and_increments_revision(self) -> None:
        article_id = uuid.uuid4()
        actor = _actor()
        version = _version(article_id)
        session = _session(article_id, version.id, revision=2)
        incoming = {"blocks": [{"value": "نص جديد"}]}
        normalized = {"blocks": [{"id": "block_1", "value": "نص جديد"}]}
        db = MagicMock()

        with patch.object(
            article_session_service,
            "_current_draft_article_and_version",
            return_value=(_article(article_id), version),
        ), patch.object(
            article_session_service,
            "get_or_create_session",
            return_value=(session, {"blocks": []}),
        ), patch.object(
            article_session_service.butex_worker_client,
            "normalize_document",
            return_value=normalized,
        ) as normalize, patch.object(
            article_session_service,
            "_lock_current_session",
            return_value=session,
        ), patch.object(
            article_session_service.s3,
            "put_json_at",
        ) as put_json_at:
            result = article_session_service.update_session_document(
                db,
                article_id,
                actor,
                2,
                incoming,
            )

        normalize.assert_called_once_with(incoming)
        self.assertEqual(result["revision"], 3)
        self.assertEqual(result["document"], normalized)
        self.assertEqual(session.revision, 3)
        self.assertTrue(
            any(
                call.args[1] == "session/document.json"
                for call in put_json_at.call_args_list
            )
        )

    def test_discard_session_deletes_db_row_and_s3_folder(self) -> None:
        article_id = uuid.uuid4()
        session = _session(article_id, uuid.uuid4())
        db = MagicMock()

        with patch.object(
            article_session_service.article_service,
            "assert_is_author",
        ), patch.object(
            article_session_service,
            "_select_current_session",
            return_value=session,
        ), patch.object(
            article_session_service.s3,
            "delete_prefix",
        ) as delete_prefix:
            article_session_service.discard_session(db, article_id, _actor())

        db.delete.assert_called_once_with(session)
        db.commit.assert_called_once_with()
        delete_prefix.assert_called_once_with(f"articles/{article_id}/session/")


if __name__ == "__main__":
    unittest.main()
