import json
import uuid
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleDraftRevision,
    ArticleVersion,
    DraftCommandReceipt,
)
from app.models.base import Base
from app.models.user import User
from app.schemas.article import DocumentCommandPayload
from app.services import article_draft_service, article_service, burhan_client


def _english_math(expr: str = "x", opening: str = "$", closing: str = "$") -> str:
    return json.dumps(
        {
            "node_type": "MathObject",
            "math_mode": opening,
            "closing": closing,
            "superscript": None,
            "subscript": None,
            "lines": [
                {
                    "node_type": "ChainClass",
                    "chain": [
                        {
                            "node_type": "CharObject",
                            "expr": expr,
                            "superscript": None,
                            "subscript": None,
                        }
                    ],
                }
            ],
        },
        ensure_ascii=False,
    )


def test_compact_math_command_schema_accepts_normal_latex() -> None:
    payload = DocumentCommandPayload.model_validate(
        {
            "command_id": str(uuid.uuid4()),
            "base_revision": 3,
            "command": {
                "op": "replace_inline_token",
                "field_id": "field_1",
                "token_id": "math_1",
                "token": {
                    "kind": "math",
                    "latex": r"\frac{x}{2}",
                    "display": True,
                    "label": "eq:test",
                },
            },
        }
    )

    assert payload.command.token.kind == "math"
    assert payload.command.token.latex == r"\frac{x}{2}"
    assert payload.command.token.display is True


def test_inline_label_is_rejected() -> None:
    with pytest.raises(ValueError):
        DocumentCommandPayload.model_validate(
            {
                "command_id": str(uuid.uuid4()),
                "base_revision": 1,
                "command": {
                    "op": "insert_inline_token",
                    "field_id": "field_1",
                    "anchor": {"end": True},
                    "token": {
                        "kind": "math",
                        "latex": "x=1",
                        "display": False,
                        "label": "eq:nope",
                    },
                },
            }
        )


def test_editor_tree_replaces_multi_variable_run_in_rtl_order() -> None:
    tree = burhan_client._editor_math_object(
        _english_math("mc"),
        {"m": "م", "c": "س"},
        display=False,
        label=None,
    )

    char = tree["lines"][0]["chain"][0]
    assert char["expr"] == "سم"
    assert tree["source_side"] == "arabic"
    assert tree["source_owner"] == "editor"
    assert "superscript" not in tree
    assert "subscript" not in tree


def test_display_label_is_attached_to_editor_tree() -> None:
    tree = burhan_client._editor_math_object(
        _english_math("x", r"\[", r"\]"),
        {"x": "س"},
        display=True,
        label="eq:one",
    )

    assert tree["label_enabled"] is True
    assert tree["label"] == "eq:one"


def test_delimiter_display_mismatch_is_rejected() -> None:
    with pytest.raises(HTTPException) as raised:
        burhan_client._split_latex("$x$", display=True)

    assert raised.value.status_code == 422
    assert raised.value.detail["code"] == "math_display_mismatch"


def test_convert_calls_burhan_and_returns_strict_editor_token(monkeypatch) -> None:
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, path, json):
            captured["path"] = path
            captured["payload"] = json
            return httpx.Response(
                200,
                json={
                    "arabic": "$س$",
                    "mappings": {"x": "س"},
                    "english_json": _english_math("x"),
                    "status": "ok",
                    "warnings": [],
                },
            )

    monkeypatch.setattr(burhan_client.settings, "burhan_url", "http://burhan")
    monkeypatch.setattr(burhan_client.settings, "burhan_model_tier", "heuristic")
    monkeypatch.setattr(burhan_client.httpx, "Client", FakeClient)

    token, mappings = burhan_client.convert_latex_to_math_token(
        "x",
        display=False,
        label=None,
        mappings={},
    )

    assert captured["path"] == "/convert"
    assert captured["payload"]["opening"] == "$"
    assert captured["payload"]["inner_content"] == "x"
    assert captured["payload"]["model_tier"] == "heuristic"
    assert token["source"] == "$س$"
    assert token["math_object"]["lines"][0]["chain"][0]["expr"] == "س"
    assert mappings == {"x": "س"}


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
        id=uuid.uuid4(),
        clerk_id="math-command-user",
        email="math-command@example.com",
        full_name="Math Command User",
        affiliation=None,
        bio=None,
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
        yield db, user
    db.close()


def _actor(user: User) -> Actor:
    return Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method="agent",
        scopes=frozenset({"articles:read", "articles:draft:write"}),
    )


def _strict_token() -> dict:
    return {
        "kind": "math",
        "source": "$س$",
        "math_object": {
            "node_type": "MathObject",
            "math_mode": "$",
            "closing": "$",
            "source_side": "arabic",
            "source_owner": "editor",
            "lines": [
                {
                    "node_type": "ChainClass",
                    "chain": [{"node_type": "CharObject", "expr": "س"}],
                }
            ],
        },
    }


def test_apply_math_command_commits_mapping_and_replay_skips_burhan(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    command_id = uuid.uuid4()
    payload = DocumentCommandPayload.model_validate(
        {
            "command_id": str(command_id),
            "base_revision": 1,
            "command": {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "anchor": {"end": True},
                "token": {"kind": "math", "latex": "x", "display": False},
            },
        }
    )
    captured = {}

    def apply_worker(document, command):
        captured["command"] = command
        return {**document, "blocks": [{"id": "block_math"}]}

    with (
        patch(
            "app.services.burhan_client.convert_latex_to_math_token",
            return_value=(_strict_token(), {"x": "س"}),
        ) as convert,
        patch(
            "app.services.butex_worker_client.apply_document_command",
            side_effect=apply_worker,
        ),
    ):
        first = article_draft_service.apply_command(db, article.id, _actor(user), payload)
        replay = article_draft_service.apply_command(db, article.id, _actor(user), payload)

    db.refresh(article)
    assert first["revision_number"] == 2
    assert replay["revision_number"] == 2
    assert article.equation_mappings == {"x": "س"}
    assert convert.call_count == 1
    assert "latex" not in captured["command"]["token"]
    assert captured["command"]["token"]["math_object"]["source_owner"] == "editor"


def test_failed_worker_does_not_persist_new_mapping(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    payload = DocumentCommandPayload.model_validate(
        {
            "command_id": str(uuid.uuid4()),
            "base_revision": 1,
            "command": {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "anchor": {"end": True},
                "token": {"kind": "math", "latex": "x", "display": False},
            },
        }
    )

    with (
        patch(
            "app.services.burhan_client.convert_latex_to_math_token",
            return_value=(_strict_token(), {"x": "س"}),
        ),
        patch(
            "app.services.butex_worker_client.apply_document_command",
            side_effect=HTTPException(status_code=422, detail="bad command"),
        ),
    ):
        with pytest.raises(HTTPException):
            article_draft_service.apply_command(db, article.id, _actor(user), payload)

    db.refresh(article)
    assert article.equation_mappings == {}
    assert article.draft_revision_number == 1
