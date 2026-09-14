from __future__ import annotations

import uuid
import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.core.actor import Actor
from app.models.article import Article, ArticleSession, ArticleVersion
from app.models.enums import CompileStatus, VersionStatus
from app.routers import articles
from app.services import article_session_service, compile_service


def _objects(revision: int = 4):
    article_id = uuid.uuid4()
    article = Article(
        id=article_id,
        submitted_by=uuid.uuid4(),
        title="عنوان",
        abstract=None,
    )
    version = ArticleVersion(
        id=uuid.uuid4(),
        article_id=article_id,
        version_number=1,
        storage_prefix=f"articles/{article_id}/versions/v1/",
        status=VersionStatus.DRAFT,
        compile_status=CompileStatus.PENDING,
    )
    session = ArticleSession(
        id=uuid.uuid4(),
        article_id=article_id,
        article_version_id=version.id,
        revision=revision,
        last_saved_revision=2,
        created_by=uuid.uuid4(),
        updated_by=uuid.uuid4(),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    actor = Actor(
        user_id=article.submitted_by,
        clerk_id="user_test",
        auth_method="agent",
    )
    return article_id, article, version, session, actor


def test_prepare_session_compile_saves_exports_and_preflights_assets() -> None:
    article_id, article, version, session, actor = _objects()
    document = {"node_type": "DocumentObject", "blocks": []}
    compile_id = uuid.uuid4()
    db = MagicMock()

    def begin(*args):
        version.active_compile_id = compile_id
        version.active_compile_session_id = session.id
        version.active_compile_session_revision = session.revision
        version.compile_status = CompileStatus.PROCESSING
        return version, compile_id

    status = {
        "status": CompileStatus.PROCESSING,
        "compile_id": compile_id,
        "requested_revision": 4,
        "compiled_revision": None,
        "current_revision": 4,
        "last_saved_revision": 4,
        "pdf_ready": False,
        "stale": False,
        "error": None,
    }
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, document),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        return_value=session,
    ), patch.object(
        article_session_service,
        "_select_current_session",
        return_value=session,
    ), patch.object(
        article_session_service.s3, "put_json"
    ) as put_json, patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="a" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        side_effect=begin,
    ) as begin_compile, patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=True,
    ), patch.object(
        article_session_service.butex_worker_client,
        "export_document",
        return_value=("trusted latex", ["assets/a.png"]),
    ) as export, patch.object(
        article_session_service.s3, "assert_exists"
    ) as assert_exists, patch.object(
        article_session_service,
        "session_compile_status",
        return_value=status,
    ):
        result, task_args = article_session_service.prepare_session_compile(
            db, article_id, actor
        )

    put_json.assert_called_once_with(version.storage_prefix, document)
    export.assert_called_once_with(document)
    assert_exists.assert_called_once_with(version.storage_prefix, "assets/a.png")
    begin_compile.assert_called_once_with(
        db, version, "a" * 64, session.id, session.revision
    )
    assert session.last_saved_revision == session.revision
    assert result == status
    assert task_args == (
        version.id,
        compile_id,
        "trusted latex",
        ["assets/a.png"],
        "a" * 64,
        session.id,
        session.revision,
    )


def test_export_failure_happens_after_save_and_is_recorded() -> None:
    article_id, article, version, session, actor = _objects()
    compile_id = uuid.uuid4()
    error = HTTPException(
        status_code=422,
        detail={"code": "invalid_document", "message": "Invalid document"},
    )
    db = MagicMock()

    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        return_value=session,
    ), patch.object(
        article_session_service.s3, "put_json"
    ) as put_json, patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="b" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        return_value=(version, compile_id),
    ), patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=True,
    ), patch.object(
        article_session_service.butex_worker_client,
        "export_document",
        side_effect=error,
    ), patch.object(
        article_session_service.compile_service, "record_compile_failure"
    ) as record, pytest.raises(HTTPException) as raised:
        article_session_service.prepare_session_compile(db, article_id, actor)

    assert raised.value is error
    put_json.assert_called_once()
    assert session.last_saved_revision == session.revision
    record.assert_called_once_with(
        db,
        version,
        compile_id,
        code="invalid_document",
        message="Invalid document",
    )


def test_missing_asset_fails_before_background_scheduling() -> None:
    article_id, article, version, session, actor = _objects()
    compile_id = uuid.uuid4()
    db = MagicMock()
    missing = HTTPException(status_code=404, detail="not found")
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        return_value=session,
    ), patch.object(
        article_session_service.s3, "put_json"
    ), patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="b" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        return_value=(version, compile_id),
    ), patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=True,
    ), patch.object(
        article_session_service.butex_worker_client,
        "export_document",
        return_value=("trusted latex", ["assets/missing.png"]),
    ), patch.object(
        article_session_service.s3, "assert_exists", side_effect=missing
    ), patch.object(
        article_session_service.compile_service, "record_compile_failure"
    ) as record, pytest.raises(HTTPException) as raised:
        article_session_service.prepare_session_compile(db, article_id, actor)

    assert raised.value.status_code == 422
    assert raised.value.detail["code"] == "asset_not_found"
    record.assert_called_once_with(
        db,
        version,
        compile_id,
        code="asset_not_found",
        message="إحدى صور المقال المطلوبة غير موجودة.",
    )


def test_malformed_or_cross_article_asset_is_rejected_before_storage_lookup() -> None:
    article_id, article, version, session, actor = _objects()
    compile_id = uuid.uuid4()
    db = MagicMock()
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        return_value=session,
    ), patch.object(
        article_session_service.s3, "put_json"
    ), patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="d" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        return_value=(version, compile_id),
    ), patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=True,
    ), patch.object(
        article_session_service.butex_worker_client,
        "export_document",
        return_value=("trusted latex", ["../other-article/asset.png"]),
    ), patch.object(
        article_session_service.s3, "assert_exists"
    ) as assert_exists, patch.object(
        article_session_service.compile_service, "record_compile_failure"
    ) as record, pytest.raises(HTTPException) as raised:
        article_session_service.prepare_session_compile(db, article_id, actor)

    assert raised.value.status_code == 422
    assert raised.value.detail["code"] == "invalid_asset"
    assert_exists.assert_not_called()
    assert record.call_args.kwargs["code"] == "invalid_asset"


def test_revision_change_during_export_records_conflict_and_does_not_schedule() -> None:
    article_id, article, version, session, actor = _objects()
    compile_id = uuid.uuid4()
    changed_session = MagicMock(id=session.id, revision=session.revision + 1)
    db = MagicMock()
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        side_effect=[session, changed_session],
    ), patch.object(
        article_session_service.s3, "put_json"
    ), patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="f" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        return_value=(version, compile_id),
    ), patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=True,
    ), patch.object(
        article_session_service.butex_worker_client,
        "export_document",
        return_value=("trusted latex", []),
    ), patch.object(
        article_session_service.compile_service, "record_compile_failure"
    ) as record, pytest.raises(HTTPException) as raised:
        article_session_service.prepare_session_compile(db, article_id, actor)

    assert raised.value.status_code == 409
    assert raised.value.detail["code"] == "revision_conflict"
    assert record.call_args.kwargs["code"] == "revision_conflict"


def test_unavailable_compiler_is_recorded_after_session_save() -> None:
    article_id, article, version, session, actor = _objects()
    compile_id = uuid.uuid4()
    db = MagicMock()
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ), patch.object(
        article_session_service,
        "_lock_current_session",
        return_value=session,
    ), patch.object(
        article_session_service.s3, "put_json"
    ) as put_json, patch.object(
        article_session_service, "_write_meta"
    ), patch.object(
        article_session_service.compile_service,
        "hash_document",
        return_value="e" * 64,
    ), patch.object(
        article_session_service.compile_service,
        "begin_session_compile",
        return_value=(version, compile_id),
    ), patch.object(
        article_session_service.compile_service,
        "compiler_is_configured",
        return_value=False,
    ), patch.object(
        article_session_service.compile_service, "record_compile_failure"
    ) as record, pytest.raises(HTTPException) as raised:
        article_session_service.prepare_session_compile(db, article_id, actor)

    assert raised.value.status_code == 503
    assert raised.value.detail["code"] == "compiler_unavailable"
    put_json.assert_called_once()
    record.assert_called_once_with(
        db,
        version,
        compile_id,
        code="compiler_unavailable",
        message="خدمة إنشاء ملفّ المعاينة غير متاحة حالياً.",
    )


def test_begin_session_compile_rejects_locked_processing_attempt() -> None:
    _, _, version, session, _ = _objects()
    version.compile_status = CompileStatus.PROCESSING
    db = MagicMock()
    db.get.return_value = version

    with pytest.raises(HTTPException) as raised:
        compile_service.begin_session_compile(
            db,
            version,
            "a" * 64,
            session.id,
            session.revision,
        )

    assert raised.value.status_code == 409
    db.get.assert_called_once_with(
        ArticleVersion,
        version.id,
        with_for_update=True,
        populate_existing=True,
    )


@pytest.mark.parametrize(
    (
        "status",
        "requested_revision",
        "compiled_revision",
        "expected_ready",
        "expected_stale",
    ),
    [
        (CompileStatus.SUCCESS, 4, 4, True, False),
        (CompileStatus.SUCCESS, 4, 3, False, True),
        (CompileStatus.FAILED, 4, 4, False, False),
        (CompileStatus.PROCESSING, 3, None, False, True),
    ],
)
def test_session_compile_status_requires_successful_current_binding(
    status,
    requested_revision,
    compiled_revision,
    expected_ready,
    expected_stale,
) -> None:
    article_id, article, version, session, actor = _objects()
    version.compile_status = status
    version.active_compile_id = uuid.uuid4()
    version.active_compile_session_id = session.id
    version.active_compile_session_revision = requested_revision
    version.compiled_session_id = session.id if compiled_revision is not None else None
    version.compiled_session_revision = compiled_revision
    db = MagicMock()
    with patch.object(
        article_session_service,
        "_current_draft_article_and_version",
        return_value=(article, version),
    ), patch.object(
        article_session_service,
        "get_or_create_session",
        return_value=(session, {"blocks": []}),
    ):
        result = article_session_service.session_compile_status(db, article_id, actor)

    assert result["pdf_ready"] is expected_ready
    assert result["stale"] is expected_stale
    assert result["current_revision"] == 4


def test_session_pdf_blocks_stale_result() -> None:
    article_id, article, version, _, actor = _objects()
    db = MagicMock()
    with patch.object(
        articles.article_session_service,
        "lock_session_pdf_context",
        return_value=(
            article,
            version,
            {
                "stale": True,
                "pdf_ready": False,
                "current_revision": 5,
                "compiled_revision": 4,
            },
        ),
    ), pytest.raises(HTTPException) as raised:
        articles.get_article_session_pdf(article_id, actor, db)

    assert raised.value.status_code == 409
    assert raised.value.detail["code"] == "stale_compile"


def test_session_pdf_returns_only_current_bound_pdf() -> None:
    article_id, article, version, _, actor = _objects()
    user = MagicMock(full_name="اسم المؤلف")
    compile_id = uuid.uuid4()
    db = MagicMock()
    with patch.object(
        articles.article_session_service,
        "lock_session_pdf_context",
        return_value=(
            article,
            version,
            {
                "stale": False,
                "pdf_ready": True,
                "compile_id": compile_id,
                "current_revision": 4,
                "compiled_revision": 4,
            },
        ),
    ), patch.object(
        articles, "current_actor_user", return_value=user
    ), patch.object(
        articles.compile_service, "get_compiled_pdf", return_value=b"%PDF-test"
    ):
        response = articles.get_article_session_pdf(article_id, actor, db)

    assert response.body == b"%PDF-test"
    assert response.media_type == "application/pdf"
    assert response.headers["x-albayan-compile-id"] == str(compile_id)
    assert response.headers["x-albayan-session-revision"] == "4"


def test_compile_route_schedules_only_host_prepared_inputs() -> None:
    article_id, _, _, _, actor = _objects()
    tasks = BackgroundTasks()
    status = {
        "status": CompileStatus.PROCESSING,
        "compile_id": uuid.uuid4(),
        "requested_revision": 4,
        "compiled_revision": None,
        "current_revision": 4,
        "last_saved_revision": 4,
        "pdf_ready": False,
        "stale": False,
        "error": None,
    }
    args = (uuid.uuid4(), uuid.uuid4(), "latex", [], "c" * 64, uuid.uuid4(), 4)
    with patch.object(
        articles.article_session_service,
        "prepare_session_compile",
        return_value=(status, args),
    ):
        result = articles.compile_article_session(
            article_id, tasks, actor, MagicMock()
        )

    assert result == status
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].args == args


def test_compile_success_binds_pdf_to_session_revision() -> None:
    article_id, _, version, session, _ = _objects()
    compile_id = uuid.uuid4()
    version.active_compile_id = compile_id
    db = MagicMock()
    db.get.return_value = version
    with patch.object(compile_service, "_is_active", return_value=True), patch.object(
        compile_service.settings, "compiler_url", "http://compiler"
    ), patch.object(
        compile_service, "_call_compiler", return_value=b"%PDF"
    ), patch.object(
        compile_service.s3, "put_bytes"
    ), patch.object(
        compile_service, "validate_asset_keys", return_value=[]
    ):
        compile_service.compile_version(
            db,
            version.id,
            compile_id,
            "trusted latex",
            [],
            "d" * 64,
            session.id,
            session.revision,
        )

    assert version.compile_status == CompileStatus.SUCCESS
    assert version.compiled_session_id == session.id
    assert version.compiled_session_revision == session.revision
    assert version.compiled_document_hash == "d" * 64


def test_session_compile_migration_adds_and_removes_binding_fields() -> None:
    path = Path(__file__).parents[1] / "alembic/versions/015_add_session_compile_metadata.py"
    spec = importlib.util.spec_from_file_location("migration_015", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    fake_op = MagicMock()
    with patch.object(migration, "op", fake_op):
        migration.upgrade()
        migration.downgrade()

    added = [call.args[1].name for call in fake_op.add_column.call_args_list]
    assert added == [
        "active_compile_session_id",
        "active_compile_session_revision",
        "compiled_session_id",
        "compiled_session_revision",
        "compile_error_code",
        "compile_error_message",
    ]
    assert fake_op.create_check_constraint.call_count == 2
    assert fake_op.drop_constraint.call_count == 2
    assert fake_op.drop_column.call_count == 6
