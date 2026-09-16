"""Conservatively remove old, unreferenced formal-version packages."""

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
from app.models.article import ArticleVersion

logger = logging.getLogger(__name__)

_FORMAL_OBJECT = re.compile(
    r"^(?P<article>[0-9a-f-]{36})/versions/v(?P<number>[1-9][0-9]*)/[^/]+(?:/[^/]+)*$",
    re.IGNORECASE,
)


def cleanup_formal_orphans(
    db: Session,
    *,
    apply: bool = False,
    older_than: timedelta = timedelta(hours=24),
    now: datetime | None = None,
) -> dict[str, int]:
    if older_than < timedelta(hours=1):
        raise ValueError("older_than must be at least one hour")
    cutoff = (now or datetime.now(UTC)) - older_than
    referenced = set(db.scalars(select(ArticleVersion.storage_prefix)).all())
    packages: dict[str, list[datetime]] = {}
    stats = {"scanned": 0, "eligible": 0, "deleted": 0, "skipped": 0, "errors": 0}

    for row in s3.list_prefix("articles", ""):
        stats["scanned"] += 1
        match = _FORMAL_OBJECT.fullmatch(row["relative_key"])
        modified = row["last_modified"]
        if match is None or modified is None:
            stats["skipped"] += 1
            continue
        try:
            article_id = uuid.UUID(match.group("article"))
        except ValueError:
            stats["skipped"] += 1
            continue
        package = f"articles/{article_id}/versions/v{int(match.group('number'))}"
        comparable = (
            modified.replace(tzinfo=UTC)
            if modified.tzinfo is None
            else modified.astimezone(UTC)
        )
        packages.setdefault(package, []).append(comparable)

    for package, timestamps in packages.items():
        if package in referenced or any(timestamp > cutoff for timestamp in timestamps):
            stats["skipped"] += 1
            continue
        stats["eligible"] += 1
        if not apply:
            continue
        try:
            s3.delete_prefix(package)
            stats["deleted"] += 1
        except Exception:
            stats["errors"] += 1
            logger.warning("Failed to delete orphan formal package %s", package, exc_info=True)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find unreferenced formal packages. Dry-run unless --apply is set."
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--older-than-hours", type=int, default=24)
    args = parser.parse_args()
    if args.older_than_hours < 1:
        parser.error("--older-than-hours must be at least 1")
    with SessionLocal() as db:
        stats = cleanup_formal_orphans(
            db,
            apply=args.apply,
            older_than=timedelta(hours=args.older_than_hours),
        )
    mode = "apply" if args.apply else "dry-run"
    print(
        f"Formal orphan cleanup ({mode}): "
        + ", ".join(f"{key}={value}" for key, value in stats.items())
    )


if __name__ == "__main__":
    main()
