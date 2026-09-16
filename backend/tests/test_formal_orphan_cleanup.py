import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.jobs.cleanup_formal_orphans import cleanup_formal_orphans


def _row(relative_key: str, modified: datetime) -> dict:
    return {
        "relative_key": relative_key,
        "size": 1,
        "last_modified": modified,
        "content_type": None,
    }


def test_formal_cleanup_is_dry_run_and_never_targets_drafts_or_assets() -> None:
    now = datetime(2026, 9, 16, 12, tzinfo=UTC)
    referenced_article = uuid.uuid4()
    orphan_article = uuid.uuid4()
    referenced = f"articles/{referenced_article}/versions/v1"
    db = MagicMock()
    db.scalars.return_value.all.return_value = [referenced]
    rows = [
        _row(f"{referenced_article}/versions/v1/document.json", now - timedelta(days=2)),
        _row(f"{orphan_article}/versions/v2/document.json", now - timedelta(days=2)),
        _row(f"{orphan_article}/versions/v2/compiled.pdf", now - timedelta(days=2)),
        _row(f"{orphan_article}/draft/revisions/{uuid.uuid4()}/document.json", now - timedelta(days=2)),
        _row(f"{orphan_article}/draft/assets/image.png", now - timedelta(days=2)),
    ]
    with patch(
        "app.jobs.cleanup_formal_orphans.s3.list_prefix", return_value=rows
    ), patch("app.jobs.cleanup_formal_orphans.s3.delete_prefix") as delete:
        stats = cleanup_formal_orphans(db, now=now)

    assert stats == {
        "scanned": 5,
        "eligible": 1,
        "deleted": 0,
        "skipped": 3,
        "errors": 0,
    }
    delete.assert_not_called()


def test_formal_cleanup_deletes_whole_old_orphan_package_only_with_apply() -> None:
    now = datetime(2026, 9, 16, 12, tzinfo=UTC)
    article_id = uuid.uuid4()
    old_prefix = f"articles/{article_id}/versions/v3"
    db = MagicMock()
    db.scalars.return_value.all.return_value = []
    with patch(
        "app.jobs.cleanup_formal_orphans.s3.list_prefix",
        return_value=[
            _row(f"{article_id}/versions/v3/document.json", now - timedelta(days=2)),
            _row(f"{article_id}/versions/v3/compiled.pdf", now - timedelta(days=2)),
            _row(f"{article_id}/versions/v4/document.json", now - timedelta(hours=2)),
        ],
    ), patch("app.jobs.cleanup_formal_orphans.s3.delete_prefix") as delete:
        stats = cleanup_formal_orphans(db, apply=True, now=now)

    delete.assert_called_once_with(old_prefix)
    assert stats["eligible"] == 1
    assert stats["deleted"] == 1
    assert stats["skipped"] == 1
