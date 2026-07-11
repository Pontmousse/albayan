import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import (
    Article,
    ArticleEditor,
    ArticleReviewer,
    ArticleVersion,
    Review,
)
from app.models.enums import ReviewStatus, VersionStatus
from app.services import article_service

_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_INVALID_STATUS = HTTPException(
    status_code=400, detail="حالة الإصدار غير صالحة لهذا القرار."
)
_DRAFT_BLOCKED = HTTPException(
    status_code=400,
    detail="لا يمكن اتخاذ قرار تحريري على مسودة — يجب تقديم المقال أولاً.",
)

_DECISION_ALLOWED = {
    VersionStatus.UNDER_REVIEW,
    VersionStatus.ACCEPTED,
    VersionStatus.REJECTED,
}

_STATUS_AR = {
    VersionStatus.UNDER_REVIEW: "قيد المراجعة",
    VersionStatus.ACCEPTED: "قبول",
    VersionStatus.REJECTED: "رفض",
}


def assert_is_editor(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> ArticleEditor:
    assignment = db.scalar(
        select(ArticleEditor).where(
            ArticleEditor.article_id == article_id,
            ArticleEditor.user_id == user_id,
        )
    )
    if not assignment:
        raise _NOT_FOUND
    return assignment


def count_submitted_reviews_for_version(
    article: Article, version_id: uuid.UUID
) -> int:
    count = 0
    for assignment in article.reviewer_assignments:
        for review in assignment.reviews:
            if (
                review.status == ReviewStatus.SUBMITTED
                and review.article_version_id == version_id
            ):
                count += 1
    return count


def list_articles_for_editor(
    db: Session, user_id: uuid.UUID
) -> list[tuple[Article, ArticleVersion, int]]:
    articles = (
        db.scalars(
            select(Article)
            .join(ArticleEditor, ArticleEditor.article_id == Article.id)
            .where(ArticleEditor.user_id == user_id)
            .options(
                selectinload(Article.versions),
                selectinload(Article.reviewer_assignments).selectinload(
                    ArticleReviewer.reviews
                ),
            )
            .order_by(Article.updated_at.desc())
        )
        .unique()
        .all()
    )
    result: list[tuple[Article, ArticleVersion, int]] = []
    for article in articles:
        if not article.versions:
            continue
        latest = max(article.versions, key=lambda v: v.version_number)
        reviews_count = count_submitted_reviews_for_version(article, latest.id)
        result.append((article, latest, reviews_count))
    return result


def get_article_for_editor(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> Article:
    assert_is_editor(db, article_id, user_id)
    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .options(
            selectinload(Article.versions),
            selectinload(Article.reviewer_assignments).selectinload(
                ArticleReviewer.reviews
            ),
            selectinload(Article.reviewer_assignments).selectinload(
                ArticleReviewer.user
            ),
        )
    )
    if not article:
        raise _NOT_FOUND
    return article


def submitted_reviews_for_version(
    article: Article, version_id: uuid.UUID
) -> list[tuple[ArticleReviewer, Review]]:
    rows: list[tuple[ArticleReviewer, Review]] = []
    for assignment in article.reviewer_assignments:
        for review in assignment.reviews:
            if (
                review.status == ReviewStatus.SUBMITTED
                and review.article_version_id == version_id
            ):
                rows.append((assignment, review))
    rows.sort(
        key=lambda pair: pair[1].submitted_at or pair[1].created_at,
        reverse=True,
    )
    return rows


def apply_decision(
    db: Session,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    status: VersionStatus,
    reason: str | None = None,
) -> ArticleVersion:
    if status not in _DECISION_ALLOWED:
        raise _INVALID_STATUS
    assert_is_editor(db, article_id, user_id)
    version = article_service.current_version(db, article_id)
    if version.status == VersionStatus.DRAFT:
        raise _DRAFT_BLOCKED

    version.status = status
    if status == VersionStatus.UNDER_REVIEW and version.submitted_at is None:
        version.submitted_at = datetime.now(timezone.utc)

    label = _STATUS_AR[status]
    summary = f"قرار تحريري: {label}"
    if reason and reason.strip():
        summary = f"{summary} — {reason.strip()}"
    version.change_summary = summary

    db.commit()
    db.refresh(version)
    return version
