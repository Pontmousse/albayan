"""Issue #218: structured used-unit inventory and revision-safe apply."""

import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import (
    Article, ArticleAuthor, ArticleDraftRevision, ArticleVersion, DraftCommandReceipt,
)
from app.models.base import Base
from app.models.user import User
from app.models.enums import ArticleStatus, DraftRevisionReason
from app.services import (
    article_draft_service, article_service, used_unit_service,
)


REGISTRY = {
    "units": {
        "kg": {"name_en": "kilogram", "name_ar": "الكيلوغرام",
               "default_display": "كلغ", "alternatives": ["كغ"], "group": "mass"},
        "N": {"name_en": "newton", "name_ar": "النيوتن",
              "default_display": "ن", "alternatives": [], "group": "mechanics"},
    }
}
EMPTY = {"overrides": {}, "custom_units": {}}
KG = {"overrides": {"kg": "كغ"}, "custom_units": {}}


def math_node(*tokens):
    return {
        "node_type": "MathObject", "math_mode": "$", "closing": "$",
        "lines": [{"node_type": "ChainClass", "chain": [
            {"node_type": "CharObject", "expr": "N"},  # not a unit
            {"node_type": "CommandObject", "name": "\\mathbb", "mandatory_args": [
                {"node_type": "ChainClass", "chain": [
                    {"node_type": "CharObject", "expr": "N"}]}]},
            *[{"node_type": "CommandObject", "name": "\\unit",
               "source_latex": f"\\mathsf{{{token}}}",
               "mandatory_args": [{"node_type": "ChainClass", "chain": [
                   {"node_type": "CharObject", "expr": token}]}]}
              for token in tokens],
        ]}],
    }


def document(*maths):
    return {
        "node_type": "DocumentObject",
        "meta": {"title": "عنوان", "abstract": ""},
        "blocks": [
            {
                "id": "paragraph",
                "command": "\\paragraph",
                "value": "$x$" * len(maths),
                "inline_ids": {
                    "field_id": "field1",
                    "tokens": [{"kind": "math", "id": f"math{i}",
                                "start": i * 3, "end": i * 3 + 3}
                               for i in range(len(maths))],
                },
                "math_objects": list(maths),
            }
        ],
    }


def test_inventory_ignores_bare_variables_and_counts_unit_atoms():
    doc = document(math_node("kg", "N", "kg"), math_node("KG", "CU"))
    counts = used_unit_service.used_unit_counts(doc)
    assert counts == {"kg": 2, "N": 1, "KG": 1, "CU": 1}
    rows = used_unit_service.inventory(
        doc, {"overrides": {"kg": "كغ"},
              "custom_units": {"CU": {"display": "وحدة معايرة"}}},
        REGISTRY, revision_number=2,
    )
    indexed = {row["token"]: row for row in rows["used_units"]}
    assert indexed["kg"]["usage_count"] == 2
    assert indexed["kg"]["source"] == "article_override"
    assert indexed["kg"]["group"] == "mass"
    assert indexed["N"]["status"] == "registry"
    assert indexed["KG"]["source"] == "unknown"
    assert indexed["KG"]["group"] is None
    assert indexed["CU"]["display"] == "وحدة معايرة"
    assert len(rows["used_units"]) == 4


@pytest.fixture
def db_and_storage():
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
        id=uuid.uuid4(), clerk_id="unit-inventory-user", email="used@example.com",
        full_name="Used Unit User", affiliation=None, bio=None,
    )
    db.add(user)
    db.commit()
    storage = {}

    def put(key, value):
        assert key not in storage
        storage[key] = value

    with (
        patch("app.core.s3.put_json_key_immutable", side_effect=put),
        patch("app.core.s3.get_json_key", side_effect=lambda key: storage.get(key)),
        patch("app.core.s3.delete_key", side_effect=lambda key: storage.pop(key, None)),
        patch("app.services.butex_worker_client.normalize_document", side_effect=lambda doc: doc),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
        patch("app.services.unit_conventions_service.get_unit_registry", return_value=REGISTRY),
    ):
        article = article_service.create_article(db, user.id, "عنوان", None)
        actor = Actor(user_id=user.id, clerk_id=user.clerk_id, auth_method="human")
        yield db, article, actor
    db.close()
    engine.dispose()


def test_read_inventory_is_scoped_to_author_and_current_revision(db_and_storage):
    db, article, actor = db_and_storage
    stranger = Actor(user_id=uuid.uuid4(), clerk_id="stranger", auth_method="human")
    with pytest.raises(HTTPException) as raised:
        used_unit_service.get_inventory(db, article.id, stranger)
    assert raised.value.status_code == 404
    result = used_unit_service.get_inventory(db, article.id, actor)
    assert result["used_units"] == []
    assert result["registered_tokens"] == ["N", "kg"]


def test_changed_override_updates_only_impacted_tokens_and_revisions(db_and_storage):
    db, article, actor = db_and_storage
    initial = article_draft_service.get_draft(db, article.id, actor)
    source = document(math_node("kg"), math_node("N"))
    first = article_draft_service.put_draft(db, article.id, actor, 1, source)
    assert first["revision_number"] == 2
    observed = []
    changing = math_node("kg")
    new_math = {"node_type": "MathObject", "math_mode": "$",
                "closing": "$", "lines": changing["lines"]}

    def convert(latex, *, mappings, unit_conventions, **kwargs):
        observed.append(("convert", latex, unit_conventions))
        assert unit_conventions == KG
        return {"kind": "math", "source": "$\\unit{كغ}$",
                "math_object": new_math}, mappings

    def apply(before, command):
        observed.append(("worker", command["field_id"], command["token_id"]))
        # Simulate Document2's targeted token and text replacement.
        assert command["token_id"] == "math0"
        updated = document(new_math, math_node("N"))
        return updated

    with (
        patch("app.services.butex_worker_client.project_math_object_to_english",
              side_effect=lambda tree: tree),
        patch("app.services.burhan_reverse_client.project_math_object_to_canonical_latex",
              return_value=(r"3\\mathsf{kg}", [])),
        patch("app.services.burhan_client.convert_canonical_latex_to_math_object",
              side_effect=convert),
        patch("app.services.butex_worker_client.apply_document_command",
              side_effect=apply),
    ):
        saved = used_unit_service.apply_conventions(
            db, article.id, actor, base_revision=2, conventions=KG,
        )

    assert saved["revision_number"] == 3
    assert saved["unit_conventions"] == KG
    assert saved["affected_block_ids"] == ["paragraph"]
    assert len([item for item in observed if item[0] == "convert"]) == 1
    assert len([item for item in observed if item[0] == "worker"]) == 1
    history = article_draft_service.get_revision_history_detail(
        db, article.id, first["revision_id"], actor
    )
    assert history["unit_conventions"] == EMPTY
    assert history["document"] == source
    current = article_draft_service.get_draft(db, article.id, actor)
    assert current["unit_conventions"] == KG
    assert db.get(Article, article.id).unit_conventions == KG
    assert db.get(ArticleDraftRevision, saved["revision_id"]).reason == DraftRevisionReason.UNIT_CONVENTIONS


def test_used_custom_unit_cannot_be_deleted(db_and_storage):
    db, article, actor = db_and_storage
    article.unit_conventions = {
        "overrides": {},
        "custom_units": {"CU": {"display": "وحدة معايرة"}},
    }
    db.commit()
    article_draft_service.put_draft(
        db, article.id, actor, 1, document(math_node("CU"))
    )
    with pytest.raises(HTTPException) as raised:
        used_unit_service.apply_conventions(
            db, article.id, actor, base_revision=2, conventions=EMPTY,
        )
    assert raised.value.status_code == 409
    assert raised.value.detail["code"] == "used_custom_unit"


def test_unchanged_settings_does_not_create_revision(db_and_storage):
    db, article, actor = db_and_storage
    result = used_unit_service.apply_conventions(
        db, article.id, actor, base_revision=1, conventions=EMPTY,
    )
    assert result["revision_number"] == 1
    assert db.query(ArticleDraftRevision).count() == 1


def test_stale_base_rejected_before_conversion(db_and_storage):
    db, article, actor = db_and_storage
    with pytest.raises(HTTPException) as raised:
        used_unit_service.apply_conventions(
            db, article.id, actor, base_revision=999, conventions=KG,
        )
    assert raised.value.status_code == 409


def test_unsafe_reverse_projection_fails_without_mutation(db_and_storage):
    db, article, actor = db_and_storage
    article_draft_service.put_draft(
        db, article.id, actor, 1, document(math_node("kg"))
    )
    with (
        patch("app.services.butex_worker_client.project_math_object_to_english",
              side_effect=lambda x: x),
        patch("app.services.burhan_reverse_client.project_math_object_to_canonical_latex",
              return_value=("x", ["unmapped_arabic_variable"])),
    ):
        with pytest.raises(HTTPException) as raised:
            used_unit_service.apply_conventions(
                db, article.id, actor, base_revision=2, conventions=KG,
            )
    assert raised.value.detail["code"] == "unit_rewrite_unsafe"
    assert db.get(Article, article.id).draft_revision_number == 2
