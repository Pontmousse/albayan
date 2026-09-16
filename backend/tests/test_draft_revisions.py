import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.actor import Actor, require_actor_scope
from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleDraftRevision,
    ArticleVersion,
    DraftCommandReceipt,
)
from app.models.base import Base
from app.models.user import User
from app.models.enums import ArticleStatus
from app.schemas.article import DocumentCommandPayload
from app.services import article_draft_service, article_service


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
            DraftCommandReceipt.__table__,
        ],
    )
    db = Session(engine)
    user = User(
        id=uuid.uuid4(), clerk_id="draft-user", email="draft@example.com",
        full_name="Draft User", affiliation=None, bio=None,
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
        patch("app.services.butex_worker_client.normalize_document", side_effect=lambda value: value),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
    ):
        yield db, user, objects
    db.close()


def actor(user: User, method: str = "human") -> Actor:
    return Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method=method,
        scopes=frozenset({"articles:read", "articles:draft:write"}),
    )


def test_creation_has_revision_one_and_zero_formal_versions(db_and_storage):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", "ملخص")
    assert article.draft_revision_number == 1
    assert article.current_draft_revision_id is not None
    assert db.scalars(select(ArticleDraftRevision)).all()[0].revision_number == 1
    assert db.scalars(select(ArticleVersion)).all() == []
    assert list(objects) == [
        f"articles/{article.id}/draft/revisions/{article.current_draft_revision_id}/document.json"
    ]


def test_autosave_syncs_metadata_and_hash_noop_reuses_revision(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "قديم", None)
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    document = {**draft["document"], "meta": {"title": "جديد", "abstract": "ملخص"}}
    saved = article_draft_service.put_draft(
        db, article.id, actor(user), draft["revision_number"], document
    )
    db.refresh(article)
    assert saved["revision_number"] == 2
    assert (article.title, article.abstract) == ("جديد", "ملخص")
    noop = article_draft_service.put_draft(db, article.id, actor(user), 2, document)
    assert noop["revision_number"] == 2
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == 2


def test_stale_base_conflicts_without_moving_pointer(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(db, article.id, actor(user), 1, draft["document"] | {"blocks": [{"id": "a"}]})
    with pytest.raises(HTTPException) as raised:
        article_draft_service.put_draft(db, article.id, actor(user), 1, draft["document"])
    assert raised.value.status_code == 409
    db.refresh(article)
    assert article.draft_revision_number == 2


def test_agent_scope_is_enforced() -> None:
    agent = Actor(
        user_id=uuid.uuid4(), clerk_id="agent", auth_method="agent",
        scopes=frozenset({"articles:read"}),
    )
    with pytest.raises(HTTPException) as raised:
        require_actor_scope(agent, "articles:draft:write")
    assert raised.value.status_code == 403


def test_command_noop_still_gets_an_idempotency_receipt(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    command_id = uuid.uuid4()
    payload = DocumentCommandPayload(
        command_id=command_id,
        base_revision=1,
        command={"op": "update_document_meta", "title": "عنوان", "abstract": ""},
    )
    with patch(
        "app.services.butex_worker_client.apply_document_command",
        side_effect=lambda document, _command: document,
    ):
        result = article_draft_service.apply_command(db, article.id, actor(user, "agent"), payload)
    assert result["revision_number"] == 1
    receipt = db.get(DraftCommandReceipt, command_id)
    assert receipt is not None and receipt.result_revision_number == 1


def test_command_id_replay_rejects_a_changed_payload(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    command_id = uuid.uuid4()
    first = DocumentCommandPayload(
        command_id=command_id,
        base_revision=1,
        command={"op": "update_document_meta", "title": "عنوان", "abstract": ""},
    )
    changed = DocumentCommandPayload(
        command_id=command_id,
        base_revision=1,
        command={"op": "update_document_meta", "title": "عنوان آخر", "abstract": ""},
    )
    with patch(
        "app.services.butex_worker_client.apply_document_command",
        side_effect=lambda document, _command: document,
    ):
        article_draft_service.apply_command(db, article.id, actor(user, "agent"), first)
        with pytest.raises(HTTPException) as raised:
            article_draft_service.apply_command(
                db, article.id, actor(user, "agent"), changed
            )
    assert raised.value.status_code == 409


def test_agent_cannot_change_document_author_text(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    changed = {
        **draft["document"],
        "meta": {**draft["document"]["meta"], "authors": ["مؤلف آخر"]},
    }
    with pytest.raises(HTTPException) as raised:
        article_draft_service.put_draft(
            db, article.id, actor(user, "agent"), 1, changed
        )
    assert raised.value.status_code == 403
    assert db.scalars(select(ArticleAuthor)).all()[0].user_id == user.id


def test_revision_retention_deletes_database_row_before_snapshot(db_and_storage):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    with patch.object(article_draft_service, "REVISION_RETENTION_LIMIT", 2):
        for number in (2, 3):
            current = article_draft_service.get_draft(db, article.id, actor(user))
            article_draft_service.put_draft(
                db,
                article.id,
                actor(user),
                current["revision_number"],
                {**current["document"], "blocks": [{"id": f"block-{number}"}]},
            )
    revisions = list(
        db.scalars(
            select(ArticleDraftRevision).order_by(
                ArticleDraftRevision.revision_number
            )
        ).all()
    )
    assert [row.revision_number for row in revisions] == [2, 3]
    assert len(objects) == 2
    db.refresh(article)
    assert article.current_draft_revision_id == revisions[-1].id


def test_history_is_newest_first_and_detail_loads_lazily(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "الأول", None)
    first_id = article.current_draft_revision_id
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db,
        article.id,
        actor(user),
        1,
        {**draft["document"], "meta": {"title": "الثاني", "abstract": ""}},
    )

    history = article_draft_service.list_revision_history(db, article.id, actor(user))
    assert [item["revision_number"] for item in history] == [2, 1]
    assert history[0]["is_current"] is True
    assert history[1]["is_current"] is False
    detail = article_draft_service.get_revision_history_detail(
        db, article.id, first_id, actor(user)
    )
    assert detail["document"]["meta"]["title"] == "الأول"


def test_history_is_owner_only_but_remains_readable_after_submission(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    stranger = User(
        id=uuid.uuid4(), clerk_id="stranger", email="stranger@example.com",
        full_name="Stranger", affiliation=None, bio=None,
    )
    db.add(stranger)
    db.commit()
    with pytest.raises(HTTPException) as hidden:
        article_draft_service.list_revision_history(db, article.id, actor(stranger))
    assert hidden.value.status_code == 404

    article.status = ArticleStatus.SUBMITTED
    db.commit()
    assert len(article_draft_service.list_revision_history(db, article.id, actor(user))) == 1
    with pytest.raises(HTTPException) as frozen:
        article_draft_service.restore_revision(
            db, article.id, article.current_draft_revision_id, actor(user), 1
        )
    assert frozen.value.status_code == 409


def test_restore_creates_a_new_revision_and_syncs_metadata(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "الأول", "ملخص")
    first_id = article.current_draft_revision_id
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db,
        article.id,
        actor(user),
        1,
        {**draft["document"], "meta": {"title": "الثاني", "abstract": "آخر"}},
    )

    restored = article_draft_service.restore_revision(
        db, article.id, first_id, actor(user), 2
    )
    assert restored["revision_number"] == 3
    assert restored["reason"].value == "restore"
    assert restored["restored_from_id"] == first_id
    assert restored["restored_from_revision_number"] == 1
    db.refresh(article)
    assert (article.title, article.abstract) == ("الأول", "ملخص")
    assert len(db.scalars(select(ArticleAuthor)).all()) == 1
    restored_row = db.get(ArticleDraftRevision, restored["revision_id"])
    assert restored_row.compile_status.value == "pending"


def test_restore_records_a_revision_even_when_content_matches_current(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    first_id = article.current_draft_revision_id
    first = article_draft_service.get_draft(db, article.id, actor(user))
    second = article_draft_service.put_draft(
        db, article.id, actor(user), 1,
        {**first["document"], "meta": {"title": "B", "abstract": ""}},
    )
    article_draft_service.put_draft(
        db, article.id, actor(user), 2, first["document"]
    )
    restored = article_draft_service.restore_revision(
        db, article.id, first_id, actor(user), 3
    )
    assert second["revision_number"] == 2
    assert restored["revision_number"] == 4
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == 4


def test_restore_rejects_current_and_cross_article_revision(db_and_storage):
    db, user, _ = db_and_storage
    first = article_service.create_article(db, user.id, "A", None)
    second = article_service.create_article(db, user.id, "B", None)
    with pytest.raises(HTTPException) as current:
        article_draft_service.restore_revision(
            db, first.id, first.current_draft_revision_id, actor(user), 1
        )
    assert current.value.status_code == 409
    with pytest.raises(HTTPException) as cross_article:
        article_draft_service.restore_revision(
            db, first.id, second.current_draft_revision_id, actor(user), 1
        )
    assert cross_article.value.status_code == 404
    with pytest.raises(HTTPException) as agent_restore:
        article_draft_service.restore_revision(
            db,
            first.id,
            first.current_draft_revision_id,
            actor(user, "agent"),
            1,
        )
    assert agent_restore.value.status_code == 403


def test_retained_history_protects_known_and_phase_one_assets(db_and_storage):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    revision = db.get(ArticleDraftRevision, article.current_draft_revision_id)
    revision.referenced_asset_ids = ["assets/known.png"]
    db.commit()
    assert article_draft_service.asset_is_referenced_by_history(
        db, article.id, "assets/known.png"
    )

    revision.referenced_asset_ids = None
    objects[revision.storage_key] = {
        **objects[revision.storage_key],
        "blocks": [{"kind": "image", "assetId": "assets/legacy.png"}],
    }
    db.commit()
    with patch(
        "app.services.butex_worker_client.export_document",
        return_value=("tex", ["assets/legacy.png"]),
    ):
        assert article_draft_service.asset_is_referenced_by_history(
            db, article.id, "assets/legacy.png"
        )


def test_phase_one_asset_fallback_fails_closed_when_storage_is_unavailable(
    db_and_storage,
):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    revision = db.get(ArticleDraftRevision, article.current_draft_revision_id)
    revision.referenced_asset_ids = None
    db.commit()
    with patch(
        "app.services.article_draft_service.s3.get_json_key",
        side_effect=HTTPException(status_code=503, detail="storage unavailable"),
    ), pytest.raises(HTTPException) as blocked:
        article_draft_service.asset_is_referenced_by_history(
            db, article.id, "assets/unknown.png"
        )
    assert blocked.value.status_code == 503


def test_restore_storage_failure_does_not_move_current_pointer(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    target_id = article.current_draft_revision_id
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db, article.id, actor(user), 1,
        {**draft["document"], "meta": {"title": "B", "abstract": ""}},
    )
    with patch(
        "app.services.article_draft_service.s3.put_json_key_immutable",
        side_effect=HTTPException(status_code=503, detail="storage unavailable"),
    ), pytest.raises(HTTPException):
        article_draft_service.restore_revision(
            db, article.id, target_id, actor(user), 2
        )
    db.refresh(article)
    assert article.draft_revision_number == 2
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == 2


def test_restore_database_failure_leaves_only_an_unreferenced_candidate(
    db_and_storage,
):
    db, user, objects = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    target_id = article.current_draft_revision_id
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db, article.id, actor(user), 1,
        {**draft["document"], "meta": {"title": "B", "abstract": ""}},
    )
    with patch.object(db, "commit", side_effect=RuntimeError("database failed")):
        with pytest.raises(RuntimeError):
            article_draft_service.restore_revision(
                db, article.id, target_id, actor(user), 2
            )
    db.rollback()
    db.refresh(article)
    assert article.draft_revision_number == 2
    assert len(db.scalars(select(ArticleDraftRevision)).all()) == 2
    assert len(objects) == 3


def test_pruning_preserves_restore_source_number(db_and_storage):
    db, user, _ = db_and_storage
    article = article_service.create_article(db, user.id, "A", None)
    first_id = article.current_draft_revision_id
    draft = article_draft_service.get_draft(db, article.id, actor(user))
    article_draft_service.put_draft(
        db, article.id, actor(user), 1,
        {**draft["document"], "meta": {"title": "B", "abstract": ""}},
    )
    with patch.object(article_draft_service, "REVISION_RETENTION_LIMIT", 2):
        restored = article_draft_service.restore_revision(
            db, article.id, first_id, actor(user), 2
        )
    assert db.get(ArticleDraftRevision, first_id) is None
    restored_row = db.get(ArticleDraftRevision, restored["revision_id"])
    assert restored_row is not None
    assert restored_row.restored_from_id == first_id
    assert restored_row.restored_from_revision_number == 1


def test_removed_legacy_routes_are_absent():
    from app.routers import articles

    paths = {route.path for route in articles.router.routes if hasattr(route, "path")}
    assert not any("/session" in path for path in paths)
    assert "/api/v1/articles/{article_id}/document" not in paths
    assert "/api/v1/articles/{article_id}/compile" not in paths
    assert "/api/v1/articles/{article_id}/compile/status" not in paths
    assert "/api/v1/articles/{article_id}/pdf" not in paths
    assert "/api/v1/articles/{article_id}/draft/revisions" in paths
    assert "/api/v1/articles/{article_id}/draft/revisions/{revision_id}" in paths
    assert (
        "/api/v1/articles/{article_id}/draft/revisions/{revision_id}/restore"
        in paths
    )
