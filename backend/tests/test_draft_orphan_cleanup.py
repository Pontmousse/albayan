import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.jobs.cleanup_draft_orphans import cleanup_draft_orphans


def _inventory(relative_key: str, modified: datetime) -> dict:
    return {
        "relative_key": relative_key,
        "size": 1,
        "last_modified": modified,
        "content_type": None,
    }


def test_cleanup_is_dry_run_and_never_targets_assets_or_versions() -> None:
    now = datetime(2026, 9, 15, 12, tzinfo=UTC)
    article_id = uuid.uuid4()
    live_revision_id = uuid.uuid4()
    orphan_revision_id = uuid.uuid4()
    active_compile_id = uuid.uuid4()
    stale_compile_id = uuid.uuid4()
    live_key = (
        f"articles/{article_id}/draft/revisions/{live_revision_id}/document.json"
    )
    revision = SimpleNamespace(
        id=live_revision_id,
        article_id=article_id,
        storage_key=live_key,
        active_compile_id=active_compile_id,
    )
    db = MagicMock()
    db.scalars.return_value.all.return_value = [revision]
    rows = [
        _inventory(
            f"{article_id}/draft/revisions/{orphan_revision_id}/document.json",
            now - timedelta(days=2),
        ),
        _inventory(
            f"{article_id}/draft/revisions/{live_revision_id}/document.json",
            now - timedelta(days=2),
        ),
        _inventory(
            f"{article_id}/draft/previews/{live_revision_id}/{stale_compile_id}/compiled.pdf",
            now - timedelta(days=2),
        ),
        _inventory(
            f"{article_id}/draft/previews/{live_revision_id}/{active_compile_id}/compiled.pdf",
            now - timedelta(days=2),
        ),
        _inventory(
            f"{article_id}/draft/assets/keep.png",
            now - timedelta(days=2),
        ),
        _inventory(
            f"{article_id}/versions/v1/document.json",
            now - timedelta(days=2),
        ),
    ]
    with patch(
        "app.jobs.cleanup_draft_orphans.s3.list_prefix", return_value=rows
    ), patch("app.jobs.cleanup_draft_orphans.s3.delete_key") as delete:
        stats = cleanup_draft_orphans(db, now=now)

    assert stats == {
        "scanned": 6,
        "eligible": 2,
        "deleted": 0,
        "skipped": 4,
        "errors": 0,
    }
    delete.assert_not_called()


def test_cleanup_apply_deletes_only_old_unreferenced_objects() -> None:
    now = datetime(2026, 9, 15, 12, tzinfo=UTC)
    article_id = uuid.uuid4()
    orphan_revision_id = uuid.uuid4()
    old_key = f"{article_id}/draft/revisions/{orphan_revision_id}/document.json"
    recent_key = f"{article_id}/draft/revisions/{uuid.uuid4()}/document.json"
    db = MagicMock()
    db.scalars.return_value.all.return_value = []
    with patch(
        "app.jobs.cleanup_draft_orphans.s3.list_prefix",
        return_value=[
            _inventory(old_key, now - timedelta(days=2)),
            _inventory(recent_key, now - timedelta(hours=2)),
        ],
    ), patch("app.jobs.cleanup_draft_orphans.s3.delete_key") as delete:
        stats = cleanup_draft_orphans(db, apply=True, now=now)

    delete.assert_called_once_with(f"articles/{old_key}")
    assert stats["deleted"] == 1
    assert stats["skipped"] == 1
