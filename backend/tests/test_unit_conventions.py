"""Regression coverage for issue #217: article unit conventions + immutable revisions."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import (
    Article, ArticleAuthor, ArticleDraftRevision, ArticleVersion, DraftCommandReceipt,
)
from app.models.base import Base
from app.models.enums import ArticleStatus
from app.models.user import User
from app.routers.unit_conventions import get_unit_conventions, put_unit_conventions
from app.schemas.article import DocumentCommandPayload
from app.schemas.unit_conventions import UnitConventions
from app.services import article_draft_service, article_service, burhan_client


ORIGINAL = {
    "overrides": {"kg": "كلغ"},
    "custom_units": {"CU": {"name": "Calibration unit", "display": "وحدة معايرة"}},
}
CHANGED = {
    "overrides": {"kg": "كغ"},
    "custom_units": {"CU": {"name": "Calibration unit", "display": "وحدة معايرة"}},
}
EMPTY = {"overrides": {}, "custom_units": {}}


@pytest.fixture
def article_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__, Article.__table__, ArticleAuthor.__table__,
            ArticleDraftRevision.__table__, ArticleVersion.__table__,
            DraftCommandReceipt.__table__,
        ],
    )
    db = Session(engine)
    user = User(
        id=uuid.uuid4(), clerk_id="unit-user", email="units@example.com",
        full_name="Unit User", affiliation=None, bio=None,
    )
    db.add(user)
    db.commit()
    stored = {}

    def write_once(key, value):
        assert key not in stored
        stored[key] = value

    with (
        patch("app.core.s3.put_json_key_immutable", side_effect=write_once),
        patch("app.core.s3.get_json_key", side_effect=lambda key: stored.get(key)),
        patch("app.core.s3.delete_key", side_effect=lambda key: stored.pop(key, None)),
        patch("app.services.butex_worker_client.normalize_document", side_effect=lambda x: x),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
    ):
        article = article_service.create_article(db, user.id, "عنوان", None)
        actor = Actor(
            user_id=user.id, clerk_id=user.clerk_id, auth_method="human",
            scopes=frozenset({"articles:read", "articles:draft:write"}),
        )
        yield db, article, actor
    db.close()
    engine.dispose()


def _insert_payload(revision: int) -> DocumentCommandPayload:
    return DocumentCommandPayload.model_validate({
        "command_id": str(uuid.uuid4()),
        "base_revision": revision,
        "command": {
            "op": "insert_inline_token",
            "field_id": "field_1",
            "anchor": {"end": True},
            "token": {"kind": "math", "latex": r"3\mathsf{kg}+2\mathsf{CU}", "display": False},
        },
    })


def test_api_roundtrip_and_mappings_remain_distinct(article_db):
    db, article, actor = article_db
    assert get_unit_conventions(article.id, actor, db) == EMPTY
    initial = db.get(ArticleDraftRevision, article.current_draft_revision_id)
    assert initial.unit_conventions == EMPTY
    article.equation_mappings = {"x": "س"}
    db.commit()

    assert put_unit_conventions(article.id, UnitConventions.model_validate(ORIGINAL), actor, db) == ORIGINAL
    db.expire_all()
    assert get_unit_conventions(article.id, actor, db) == ORIGINAL
    assert db.get(Article, article.id).equation_mappings == {"x": "س"}
    assert db.get(Article, article.id).draft_revision_number == 1
    assert db.get(ArticleDraftRevision, initial.id).unit_conventions == EMPTY


def test_permission_checks_and_frozen_rejection(article_db):
    db, article, actor = article_db
    outsider = Actor(user_id=uuid.uuid4(), clerk_id="outsider", auth_method="human")
    with pytest.raises(HTTPException) as read:
        get_unit_conventions(article.id, outsider, db)
    assert read.value.status_code == 404
    with pytest.raises(HTTPException) as write:
        put_unit_conventions(article.id, UnitConventions(), outsider, db)
    assert write.value.status_code == 404

    article.status = ArticleStatus.SUBMITTED
    db.commit()
    with pytest.raises(HTTPException) as frozen:
        put_unit_conventions(article.id, UnitConventions(), actor, db)
    assert frozen.value.status_code == 409
    # A submitted article's conventions are still readable.
    assert get_unit_conventions(article.id, actor, db) == EMPTY


@pytest.mark.parametrize("raw", [
    {"overrides": {"bad token": "كغ"}},
    {"overrides": {"kg": ""}},
    {"overrides": {"kg": 3}},
    {"overrides": {"kg": "كغ"}, "custom_units": {"kg": {"name": "kg", "display": "وحدة"}}},
    {"custom_units": {"CU": {"name": "", "display": "وحدة"}}},
    {"custom_units": {"CU": {"name": "Calibration unit"}}},
    {"custom_units": {"CU": {"name": "Calibration unit", "display": "وحدة", "extra": True}}},
    {"custom_units": {"c/u": {"name": "Calibration unit", "display": "وحدة"}}},
    {"unknown": 1},
    [],
])
def test_schema_rejects_malformed_conventions(raw):
    with pytest.raises(ValidationError):
        UnitConventions.model_validate(raw)


def test_tokens_are_case_sensitive():
    conventions = UnitConventions.model_validate({
        "overrides": {"kg": "كغ", "Kg": "الوحدة الكبيرة"},
        "custom_units": {"CU": {"name": "Calibration", "display": "معايرة"}},
    })
    assert conventions.overrides["kg"] != conventions.overrides["Kg"]


def test_revision_snapshots_survive_changes_and_restoration(article_db):
    db, article, actor = article_db
    assert put_unit_conventions(article.id, UnitConventions.model_validate(ORIGINAL), actor, db) == ORIGINAL
    first = article_draft_service.put_draft(
        db, article.id, actor, 1,
        {**article_draft_service.get_draft(db, article.id, actor)["document"],
         "blocks": [{"id": "revision_A"}]},
    )
    assert first["unit_conventions"] == ORIGINAL
    assert first["revision_number"] == 2

    put_unit_conventions(article.id, UnitConventions.model_validate(CHANGED), actor, db)
    second = article_draft_service.put_draft(
        db, article.id, actor, 2,
        {**first["document"], "blocks": [{"id": "revision_B"}]},
    )
    assert second["unit_conventions"] == CHANGED
    assert second["revision_number"] == 3
    saved_a = article_draft_service.get_revision_history_detail(db, article.id, first["revision_id"], actor)
    saved_b = article_draft_service.get_revision_history_detail(db, article.id, second["revision_id"], actor)
    assert saved_a["unit_conventions"]["overrides"]["kg"] == "كلغ"
    assert saved_b["unit_conventions"]["overrides"]["kg"] == "كغ"

    restored = article_draft_service.restore_revision(db, article.id, first["revision_id"], actor, 3)
    assert restored["revision_number"] == 4
    assert restored["unit_conventions"] == ORIGINAL
    assert get_unit_conventions(article.id, actor, db) == CHANGED


def test_document2_passes_effective_conventions_separately_and_replays(article_db):
    db, article, actor = article_db
    article.equation_mappings = {"x": "س"}
    db.commit()
    put_unit_conventions(article.id, UnitConventions.model_validate(ORIGINAL), actor, db)
    seen = []
    counter = 0

    def convert(_latex, *, display, label, mappings, unit_conventions, **kwargs):
        assert "model_tier" not in kwargs
        seen.append({"mappings": mappings.copy(), "units": unit_conventions.copy()})
        return {"kind": "math", "source": "$3kg$", "math_object": {}}, mappings

    def apply_worker(document, _command):
        nonlocal counter
        counter += 1
        return {**document, "blocks": [{"id": f"math_{counter}"}]}

    with (
        patch("app.services.burhan_client.convert_canonical_latex_to_math_object", side_effect=convert) as conversion,
        patch("app.services.butex_worker_client.apply_document_command", side_effect=apply_worker),
    ):
        first_payload = _insert_payload(1)
        first = article_draft_service.apply_command(db, article.id, actor, first_payload)
        replay = article_draft_service.apply_command(db, article.id, actor, first_payload)
        assert replay["revision_id"] == first["revision_id"]
        put_unit_conventions(article.id, UnitConventions.model_validate(CHANGED), actor, db)
        second = article_draft_service.apply_command(db, article.id, actor, _insert_payload(2))

    assert conversion.call_count == 2
    assert seen == [
        {"mappings": {"x": "س"}, "units": ORIGINAL},
        {"mappings": {"x": "س"}, "units": CHANGED},
    ]
    assert first["unit_conventions"] == ORIGINAL
    assert second["unit_conventions"] == CHANGED
    assert db.get(Article, article.id).equation_mappings == {"x": "س"}


def test_concurrent_change_after_conversion_is_rejected(article_db):
    db, article, actor = article_db
    put_unit_conventions(article.id, UnitConventions.model_validate(ORIGINAL), actor, db)

    def convert(*_args, **_kwargs):
        put_unit_conventions(article.id, UnitConventions.model_validate(CHANGED), actor, db)
        return {"kind": "math", "source": "$kg$", "math_object": {}}, {}

    with (
        patch("app.services.burhan_client.convert_canonical_latex_to_math_object", side_effect=convert),
        patch("app.services.butex_worker_client.apply_document_command",
              side_effect=lambda doc, cmd: {**doc, "blocks": [{"id": "math"}]}),
    ):
        with pytest.raises(HTTPException) as error:
            article_draft_service.apply_command(db, article.id, actor, _insert_payload(1))
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "unit_conventions_conflict"
    assert db.get(Article, article.id).draft_revision_number == 1


def test_burhan_request_transmits_both_maps_and_preserves_unknown_warnings(monkeypatch):
    captured = {}
    tree = {
        "node_type": "MathObject", "math_mode": "$", "closing": "$",
        "lines": [{"node_type": "ChainClass", "chain": [
            {"node_type": "CharObject", "expr": "م", "superscript": None, "subscript": None},
        ]}],
    }

    class Client:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, path, json):
            captured["request"] = json
            return httpx.Response(200, json={
                "status": "ok", "arabic": "$م$", "arabic_json": tree,
                "mappings": {"x": "س"}, "warnings": [{"code": "unknown_unit", "message": "preserved"}],
            })

    monkeypatch.setattr(burhan_client.settings, "burhan_url", "https://burhan.local")
    monkeypatch.setattr(burhan_client.httpx, "Client", Client)
    diagnostics = {}
    token, mappings = burhan_client.convert_canonical_latex_to_math_object(
        r"3\mathsf{kg}", display=False, label=None, mappings={"x": "س"},
        unit_conventions=ORIGINAL, diagnostics=diagnostics,
    )
    assert token["kind"] == "math"
    assert mappings == {"x": "س"}
    assert captured["request"]["mappings"] == {"x": "س"}
    assert captured["request"]["unit_conventions"] == ORIGINAL
    assert diagnostics["burhan_request"]["unit_conventions"] == ORIGINAL
    assert diagnostics["warnings"][0]["code"] == "unknown_unit"


def test_burhan_unit_validation_errors_remain_distinguishable(monkeypatch):
    class Client:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, path, json):
            return httpx.Response(422, json={
                "detail": {"code": "invalid_unit_conventions", "message": "bad override"}
            })

    monkeypatch.setattr(burhan_client.settings, "burhan_url", "https://burhan.local")
    monkeypatch.setattr(burhan_client.httpx, "Client", Client)
    with pytest.raises(HTTPException) as raised:
        burhan_client.convert_canonical_latex_to_math_object(
            r"3\mathsf{kg}", display=False, label=None, mappings={},
            unit_conventions=ORIGINAL,
        )
    assert raised.value.status_code == 422
    assert raised.value.detail["code"] == "invalid_unit_conventions"
