import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.actor import Actor
from app.models.enums import CompileStatus
from app.routers import articles
from app.services import compile_service


def _actor() -> Actor:
    return Actor(
        user_id=uuid.uuid4(),
        clerk_id="draft-assets",
        auth_method="human",
    )


class Upload:
    content_type = "image/png"

    async def read(self) -> bytes:
        return b"png"


def test_asset_upload_uses_the_immutable_draft_namespace() -> None:
    article_id = uuid.uuid4()
    with patch.object(
        articles.article_draft_service, "assert_editable_author"
    ) as authorize, patch.object(
        articles.s3, "put_bytes_key_immutable"
    ) as put:
        result = asyncio.run(
            articles.upload_asset(article_id, _actor(), MagicMock(), Upload())
        )

    authorize.assert_called_once()
    key, body, content_type = put.call_args.args
    assert key.startswith(f"articles/{article_id}/draft/assets/")
    assert (body, content_type) == (b"png", "image/png")
    assert result.asset_id.startswith("assets/")


def test_asset_delete_checks_the_exact_current_document() -> None:
    article_id = uuid.uuid4()
    article = SimpleNamespace(id=article_id)
    with patch.object(
        articles.article_draft_service,
        "assert_editable_author",
        return_value=article,
    ), patch.object(
        articles.article_draft_service,
        "asset_is_referenced_by_history",
        return_value=True,
    ), patch.object(articles.s3, "delete_key") as delete:
        with pytest.raises(HTTPException) as raised:
            articles.delete_asset(article_id, "photo.png", _actor(), MagicMock())

    assert raised.value.status_code == 409
    delete.assert_not_called()


def test_preview_freshness_is_bound_to_one_revision() -> None:
    successful = SimpleNamespace(
        compile_status=CompileStatus.SUCCESS,
        active_compile_id=uuid.uuid4(),
        compiled_at=datetime.now(UTC),
    )
    compile_service.assert_fresh_preview_for_submit(successful)

    newer = SimpleNamespace(
        compile_status=CompileStatus.PENDING,
        active_compile_id=None,
        compiled_at=None,
    )
    with pytest.raises(HTTPException) as raised:
        compile_service.assert_fresh_preview_for_submit(newer)
    assert raised.value.status_code == 409


def test_stale_compile_worker_does_not_write_a_pdf() -> None:
    compile_id = uuid.uuid4()
    revision = SimpleNamespace(
        id=uuid.uuid4(),
        article_id=uuid.uuid4(),
        revision_number=2,
        active_compile_id=compile_id,
    )
    db = MagicMock()
    db.get.return_value = revision

    calls = iter([True, False])
    with patch.object(
        compile_service, "_is_active", side_effect=lambda *_args: next(calls)
    ), patch.object(
        compile_service, "_call_compiler", return_value=b"%PDF"
    ), patch.object(
        compile_service.s3, "put_bytes_key_immutable"
    ) as put:
        compile_service.compile_revision(db, revision.id, compile_id, "tex", [])

    put.assert_not_called()
    db.commit.assert_not_called()
