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


def _arabic_math(
    expr: str = r"\text{س}", opening: str = "$", closing: str = "$"
) -> str:
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


def _arabic_command_math(name: str, opening: str = "$", closing: str = "$") -> str:
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
                            "node_type": "CommandObject",
                            "name": name,
                            "optional_args": [],
                            "mandatory_args": [],
                            "superscript": None,
                            "subscript": None,
                        }
                    ],
                }
            ],
        },
        ensure_ascii=False,
    )


@pytest.mark.parametrize(
    "latex",
    [
        r"\frac{x}{2}",
        r"A^\top + T",
        *[rf"R+\mathbb{{{symbol}}}" for symbol in "NZQRCH"],
        r"d+\frac{\mathrm{d}f}{\mathrm{d}x}",
        r"\mathtt{var}_0",
        r"\mathtt{sin}+\sin x",
        r"m+3\mathsf{m}",
        r"N+\mathbb{N}+3\mathsf{N}",
        r"3\unit{m}",
        r"\boxed{\frac{x_1}{\sqrt{1+x^2}}}",
    ],
)
def test_compact_math_command_schema_accepts_normal_latex(latex: str) -> None:
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
                    "latex": latex,
                    "display": True,
                    "label": "eq:test",
                },
            },
        }
    )

    assert payload.command.token.kind == "math"
    assert payload.command.token.latex == latex
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


def test_arabic_math_object_preserves_burhan_command_structure() -> None:
    tree = burhan_client._arabic_math_object(
        _arabic_command_math(r"\ad"),
        display=False,
        label=None,
    )

    node = tree["lines"][0]["chain"][0]
    assert node["node_type"] == "CommandObject"
    assert node["name"] == r"\ad"
    assert tree["source_side"] == "arabic"
    assert tree["source_owner"] == "editor"
    assert "superscript" not in tree
    assert "subscript" not in tree


def test_arabic_math_object_preserves_source_latex_and_drops_burhan_unit_metadata() -> None:
    raw = json.loads(_arabic_command_math(r"\unit"))
    node = raw["lines"][0]["chain"][0]
    node["mandatory_args"] = [
        {
            "node_type": "ChainClass",
            "chain": [
                {
                    "node_type": "CharObject",
                    "expr": "م",
                    "superscript": None,
                    "subscript": None,
                }
            ],
        }
    ]
    node["source_latex"] = r"\mathsf{m}"
    node["arabic_unit"] = r"\unit{م}"

    tree = burhan_client._arabic_math_object(raw, display=False, label=None)

    projected = tree["lines"][0]["chain"][0]
    assert projected["source_latex"] == r"\mathsf{m}"
    assert "arabic_unit" not in projected
    assert projected["mandatory_args"][0]["chain"][0]["expr"] == "م"


def test_display_label_is_attached_without_rewriting_arabic_tree() -> None:
    tree = burhan_client._arabic_math_object(
        _arabic_math(r"\text{س}", r"\[", r"\]"),
        display=True,
        label="eq:one",
    )

    assert tree["lines"][0]["chain"][0]["expr"] == r"\text{س}"
    assert tree["label_enabled"] is True
    assert tree["label"] == "eq:one"


def test_delimiter_display_mismatch_is_rejected() -> None:
    with pytest.raises(HTTPException) as raised:
        burhan_client._split_latex("$x$", display=True)

    assert raised.value.status_code == 422
    assert raised.value.detail["code"] == "math_display_mismatch"


def test_convert_calls_burhan_and_uses_returned_arabic_json(monkeypatch) -> None:
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
                    "arabic": r"$\ad$",
                    "mappings": {"d": r"\ad"},
                    "english_json": _english_math("d"),
                    "arabic_json": _arabic_command_math(r"\ad"),
                    "status": "ok",
                    "warnings": [],
                },
            )

    monkeypatch.setattr(burhan_client.settings, "burhan_url", "http://burhan")
    monkeypatch.setattr(burhan_client.settings, "burhan_model_tier", "heuristic")
    monkeypatch.setattr(burhan_client.httpx, "Client", FakeClient)

    token, mappings = burhan_client.convert_latex_to_math_token(
        "d",
        display=False,
        label=None,
        mappings={},
    )

    assert captured["path"] == "/convert"
    assert captured["payload"]["opening"] == "$"
    assert captured["payload"]["inner_content"] == "d"
    assert captured["payload"]["model_tier"] == "heuristic"
    assert token["source"] == r"$\ad$"
    node = token["math_object"]["lines"][0]["chain"][0]
    assert node["node_type"] == "CommandObject"
    assert node["name"] == r"\ad"
    assert mappings == {"d": r"\ad"}


def test_convert_rejects_missing_arabic_json(monkeypatch) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, _path, json):
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

    with pytest.raises(HTTPException) as raised:
        burhan_client.convert_latex_to_math_token(
            "x", display=False, label=None, mappings={}
        )

    assert raised.value.status_code == 502
    assert raised.value.detail["code"] == "invalid_burhan_response"


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


def _actor(user: User, *, auth_method: str = "agent") -> Actor:
    return Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method=auth_method,
        scopes=frozenset({"articles:read", "articles:draft:write"}),
    )


def test_human_authoring_also_uses_deterministic_canonical_tier(db_and_storage) -> None:
    """Authentication must not choose mathematical semantics for canonical interop."""
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    captured: dict = {}

    def convert(latex, *, display, label, mappings, diagnostics=None):
        captured["latex"] = latex
        return _strict_token(), {"x": "س"}

    with (
        patch(
            "app.services.burhan_client.convert_canonical_latex_to_math_object",
            side_effect=convert,
        ) as convert_mock,
        patch(
            "app.services.butex_worker_client.apply_document_command",
            side_effect=lambda document, _command: {
                **document,
                "blocks": [{"id": "block_math"}],
            },
        ),
    ):
        article_draft_service.apply_command(
            db, article.id, _actor(user, auth_method="human"), _insert_payload(1, "x")
        )

    assert convert_mock.call_count == 1
    assert captured["latex"] == "x"


def _strict_token(expr: str = "س") -> dict:
    return {
        "kind": "math",
        "source": f"${expr}$",
        "math_object": {
            "node_type": "MathObject",
            "math_mode": "$",
            "closing": "$",
            "source_side": "arabic",
            "source_owner": "editor",
            "lines": [
                {
                    "node_type": "ChainClass",
                    "chain": [{"node_type": "CharObject", "expr": expr}],
                }
            ],
        },
    }


def _insert_payload(base_revision: int, latex: str) -> DocumentCommandPayload:
    return DocumentCommandPayload.model_validate(
        {
            "command_id": str(uuid.uuid4()),
            "base_revision": base_revision,
            "command": {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "anchor": {"end": True},
                "token": {"kind": "math", "latex": latex, "display": False},
            },
        }
    )


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
            "app.services.burhan_client.convert_canonical_latex_to_math_object",
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


def test_consecutive_equations_reuse_and_accumulate_article_mappings(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    seen_mappings = []
    conversion_results = [
        (_strict_token("س"), {"x": "س"}),
        (_strict_token("ص"), {"x": "س", "y": "ص"}),
    ]

    def convert(_latex, *, display, label, mappings, **kwargs):
        assert display is False
        assert label is None
        # Canonical interop wrapper must not expose a caller-selected tier.
        assert "model_tier" not in kwargs
        seen_mappings.append(dict(mappings))
        return conversion_results[len(seen_mappings) - 1]

    counter = 0

    def apply_worker(document, _command):
        nonlocal counter
        counter += 1
        return {**document, "blocks": [{"id": f"block_math_{counter}"}]}

    with (
        patch(
            "app.services.burhan_client.convert_canonical_latex_to_math_object",
            side_effect=convert,
        ),
        patch(
            "app.services.butex_worker_client.apply_document_command",
            side_effect=apply_worker,
        ),
    ):
        first = article_draft_service.apply_command(
            db, article.id, _actor(user), _insert_payload(1, "x")
        )
        second = article_draft_service.apply_command(
            db, article.id, _actor(user), _insert_payload(2, "y")
        )

    db.refresh(article)
    assert first["revision_number"] == 2
    assert second["revision_number"] == 3
    assert seen_mappings == [{}, {"x": "س"}]
    assert article.equation_mappings == {"x": "س", "y": "ص"}


def test_failed_worker_does_not_persist_new_mapping(db_and_storage) -> None:
    db, user = db_and_storage
    article = article_service.create_article(db, user.id, "عنوان", None)
    payload = _insert_payload(1, "x")

    with (
        patch(
            "app.services.burhan_client.convert_canonical_latex_to_math_object",
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
