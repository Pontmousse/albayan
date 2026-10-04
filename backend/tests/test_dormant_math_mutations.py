"""Exercise the trusted draft mutation boundary without a live provider/worker."""

import uuid
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.article import DocumentCommandPayload
from app.services import article_draft_service as drafts


def payload(op="insert_inline_token", base_revision=1):
    command = {
        "op": op,
        "field_id": "f1",
        "token": {"kind": "math", "latex": r"A^\top + T", "authoring_profile": "canonical-v2"},
    }
    if op == "insert_inline_token":
        command["anchor"] = {"end": True}
    else:
        command["token_id"] = "t1"
    return DocumentCommandPayload.model_validate({"command_id": str(uuid.uuid4()), "base_revision": base_revision, "command": command})


@pytest.fixture
def boundary():
    db = MagicMock()
    db.get.return_value = None
    current = SimpleNamespace(revision_number=1)
    actor = SimpleNamespace(auth_method="agent")
    with ExitStack() as stack:
        stack.enter_context(patch.object(drafts, "assert_editable_author", return_value=SimpleNamespace()))
        stack.enter_context(patch.object(drafts, "get_current_revision", return_value=current))
        stack.enter_context(patch.object(drafts, "read_document", return_value={"blocks": []}))
        spies = {
            "convert": stack.enter_context(patch.object(drafts.burhan_client, "convert_latex_to_math_token")),
            "mappings": stack.enter_context(patch.object(drafts.equation_mapping_service, "get_equation_mappings")),
            "merge": stack.enter_context(patch.object(drafts.equation_mapping_service, "merged_equation_mappings")),
            "worker": stack.enter_context(patch.object(drafts.butex_worker_client, "_post")),
            "storage": stack.enter_context(patch.object(drafts.s3, "put_json_key_immutable")),
        }
        yield db, actor, spies


@pytest.mark.parametrize("op", ["insert_inline_token", "replace_inline_token"])
def test_compact_profile_fails_before_conversion_mapping_worker_or_persistence(boundary, op):
    db, actor, spies = boundary
    with pytest.raises(HTTPException) as error:
        drafts.apply_command(db, uuid.uuid4(), actor, payload(op))
    assert error.value.status_code == 422
    assert error.value.detail["code"] == "math_authoring_profile_unavailable"
    for spy in spies.values():
        spy.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_revision_conflict_precedes_dormant_guard(boundary):
    db, actor, spies = boundary
    with patch.object(drafts, "reject_dormant_math_authoring") as guard, pytest.raises(HTTPException) as error:
        drafts.apply_command(db, uuid.uuid4(), actor, payload(base_revision=2))
    assert error.value.status_code == 409
    guard.assert_not_called()
    for spy in spies.values():
        spy.assert_not_called()


def test_access_denial_precedes_dormant_guard(boundary):
    db, actor, _ = boundary
    with patch.object(drafts, "assert_editable_author", side_effect=HTTPException(403)), patch.object(drafts, "reject_dormant_math_authoring") as guard, pytest.raises(HTTPException) as error:
        drafts.apply_command(db, uuid.uuid4(), actor, payload())
    assert error.value.status_code == 403
    guard.assert_not_called()
    db.get.assert_not_called()


def test_receipt_replay_stays_before_dormant_guard(boundary):
    db, actor, spies = boundary
    db.get.return_value = SimpleNamespace()
    with patch.object(drafts, "_receipt_result", return_value=(SimpleNamespace(), {"blocks": []}, [])), patch.object(drafts, "revision_response", return_value={"revision_number": 2}), patch.object(drafts, "reject_dormant_math_authoring") as guard:
        result = drafts.apply_command(db, uuid.uuid4(), actor, payload())
    assert result["ok"] is True
    guard.assert_not_called()
    for spy in spies.values():
        spy.assert_not_called()


def test_full_put_autosave_stops_before_worker_storage_and_receipt(boundary):
    db, actor, spies = boundary
    document = {"blocks": [{"tokens": [{"math_object": {"authoring_profile": "canonical-v2"}}]}]}
    with pytest.raises(HTTPException) as error:
        drafts.put_draft(db, uuid.uuid4(), actor, 1, document)
    assert error.value.status_code == 422
    for spy in spies.values():
        spy.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_restore_uses_the_same_guarded_normalization(boundary):
    db, _, spies = boundary
    article_id = uuid.uuid4()
    article = SimpleNamespace(id=article_id, status=next(iter(drafts._EDITABLE_STATUSES)))
    current = SimpleNamespace(id=uuid.uuid4(), revision_number=1)
    target = SimpleNamespace(id=uuid.uuid4(), article_id=article_id, revision_number=0)
    db.scalar.return_value = article
    db.get.return_value = target
    document = {"blocks": [{"math_object": {"canonical_command": r"\mathbf"}}]}
    with patch.object(drafts, "assert_editable_author", return_value=article), patch.object(drafts, "get_current_revision", return_value=current), patch.object(drafts, "read_document", return_value=document), pytest.raises(HTTPException) as error:
        drafts.restore_revision(db, article_id, target.id, SimpleNamespace(auth_method="human"), 1)
    assert error.value.status_code == 422
    for spy in spies.values():
        spy.assert_not_called()
    db.add.assert_not_called()
