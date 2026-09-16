"""Conservatively remove unreferenced immutable draft snapshots and previews."""

from __future__ import annotations

import argparse
import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import s3
from app.core.database import SessionLocal
from app.models.article import ArticleDraftRevision

logger = logging.getLogger(__name__)

_REVISION_OBJECT = re.compile(
    r"^(?P<article>[0-9a-f-]{36})/draft/revisions/"
    r"(?P<revision>[0-9a-f-]{36})/document\.json$",
    re.IGNORECASE,
)
_PREVIEW_OBJECT = re.compile(
    r"^(?P<article>[0-9a-f-]{36})/draft/previews/"
    r"(?P<revision>[0-9a-f-]{36})/(?P<compile>[0-9a-f-]{36})/"
    r"(?:compiled\.pdf|compile\.log)$",
    re.IGNORECASE,
)


def cleanup_draft_orphans(
    db: Session,
    *,
    apply: bool = False,
    older_than: timedelta = timedelta(hours=24),
    now: datetime | None = None,
) -> dict[str, int]:
    if older_than < timedelta(hours=1):
        raise ValueError("older_than must be at least one hour")
    cutoff = (now or datetime.now(UTC)) - older_than
    revisions = list(db.scalars(select(ArticleDraftRevision)).all())
    snapshot_keys = {revision.storage_key for revision in revisions}
    active_previews = {
        (revision.article_id, revision.id, revision.active_compile_id)
        for revision in revisions
        if revision.active_compile_id is not None
    }
    stats = {"scanned": 0, "eligible": 0, "deleted": 0, "skipped": 0, "errors": 0}

    for row in s3.list_prefix("articles", ""):
        stats["scanned"] += 1
        relative_key = row["relative_key"]
        revision_match = _REVISION_OBJECT.fullmatch(relative_key)
        preview_match = _PREVIEW_OBJECT.fullmatch(relative_key)
        if revision_match is None and preview_match is None:
            stats["skipped"] += 1
            continue
        last_modified = row["last_modified"]
        if last_modified is None:
            stats["skipped"] += 1
            continue
        comparable_modified = (
            last_modified.replace(tzinfo=UTC)
            if last_modified.tzinfo is None
            else last_modified.astimezone(UTC)
        )
        if comparable_modified > cutoff:
            stats["skipped"] += 1
            continue

        full_key = f"articles/{relative_key}"
        orphan = False
        try:
            if revision_match is not None:
                uuid.UUID(revision_match.group("article"))
                uuid.UUID(revision_match.group("revision"))
                orphan = full_key not in snapshot_keys
            else:
                assert preview_match is not None
                identity = (
                    uuid.UUID(preview_match.group("article")),
                    uuid.UUID(preview_match.group("revision")),
                    uuid.UUID(preview_match.group("compile")),
                )
                orphan = identity not in active_previews
        except (ValueError, AssertionError):
            stats["skipped"] += 1
            continue

        if not orphan:
            stats["skipped"] += 1
            continue
        stats["eligible"] += 1
        if not apply:
            continue
        try:
            s3.delete_key(full_key)
            stats["deleted"] += 1
        except Exception:
            stats["errors"] += 1
            logger.warning("Failed to delete orphan draft object %s", full_key, exc_info=True)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Find unreferenced draft revision/preview objects. Dry-run unless --apply is set."
        )
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--older-than-hours", type=int, default=24)
    args = parser.parse_args()
    if args.older_than_hours < 1:
        parser.error("--older-than-hours must be at least 1")
    with SessionLocal() as db:
        stats = cleanup_draft_orphans(
            db,
            apply=args.apply,
            older_than=timedelta(hours=args.older_than_hours),
        )
    mode = "apply" if args.apply else "dry-run"
    print(
        f"Draft orphan cleanup ({mode}): "
        + ", ".join(f"{key}={value}" for key, value in stats.items())
    )


if __name__ == "__main__":
    main()
