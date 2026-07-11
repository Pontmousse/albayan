import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleEditor,
    ArticleReviewer,
    ArticleVersion,
)
from app.models.enums import ReviewerAssignmentStatus, VersionStatus
from app.models.user import User
from app.services import article_service

_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_USER_NOT_FOUND = HTTPException(status_code=404, detail="المستخدم غير موجود.")
_ALREADY_ASSIGNED = HTTPException(status_code=409, detail="المستخدم معيّن بالفعل على هذا المقال.")
_ASSIGNMENT_NOT_FOUND = HTTPException(status_code=404, detail="التعيين غير موجود.")
_INVALID_STATUS = HTTPException(
    status_code=400,
    detail="حالة الإصدار غير صالحة للتجاوز.",
)

_OVERRIDE_ALLOWED = {
    VersionStatus.SUBMITTED,
    VersionStatus.UNDER_REVIEW,
    VersionStatus.ACCEPTED,
    VersionStatus.REJECTED,
    VersionStatus.PUBLISHED,
}


def get_article_or_404(db: Session, article_id: uuid.UUID) -> Article:
    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .options(
            selectinload(Article.versions),
            selectinload(Article.author_links).selectinload(ArticleAuthor.user),
            selectinload(Article.reviewer_assignments).selectinload(
                ArticleReviewer.user
            ),
            selectinload(Article.editor_assignments).selectinload(ArticleEditor.user),
        )
    )
    if not article:
        raise _NOT_FOUND
    return article


def list_articles(
    db: Session, status: VersionStatus | None = None
) -> list[tuple[Article, ArticleVersion]]:
    articles = (
        db.scalars(
            select(Article)
            .options(
                selectinload(Article.versions),
                selectinload(Article.author_links).selectinload(ArticleAuthor.user),
                selectinload(Article.reviewer_assignments).selectinload(
                    ArticleReviewer.user
                ),
                selectinload(Article.editor_assignments).selectinload(
                    ArticleEditor.user
                ),
            )
            .order_by(Article.updated_at.desc())
        )
        .unique()
        .all()
    )
    result: list[tuple[Article, ArticleVersion]] = []
    for article in articles:
        if not article.versions:
            continue
        latest = max(article.versions, key=lambda v: v.version_number)
        if status is not None and latest.status != status:
            continue
        result.append((article, latest))
    return result


def assign_reviewer(
    db: Session,
    article_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    assigner_id: uuid.UUID | None = None,
) -> ArticleReviewer:
    article = db.get(Article, article_id)
    if not article:
        raise _NOT_FOUND
    if user_id is None:
        raise HTTPException(status_code=400, detail="يلزم تحديد user_id.")

    user = db.get(User, user_id)
    if not user:
        raise _USER_NOT_FOUND

    existing = db.scalar(
        select(ArticleReviewer).where(
            ArticleReviewer.article_id == article_id,
            ArticleReviewer.user_id == user_id,
        )
    )
    if existing:
        raise _ALREADY_ASSIGNED

    now = datetime.now(timezone.utc)
    assignment = ArticleReviewer(
        article_id=article_id,
        user_id=user_id,
        status=ReviewerAssignmentStatus.ACCEPTED,
        invited_at=now,
        accepted_at=now,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def assign_editor(
    db: Session,
    article_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    assigner_id: uuid.UUID | None = None,
) -> ArticleEditor:
    article = db.get(Article, article_id)
    if not article:
        raise _NOT_FOUND
    if user_id is None:
        raise HTTPException(status_code=400, detail="يلزم تحديد user_id.")

    user = db.get(User, user_id)
    if not user:
        raise _USER_NOT_FOUND

    existing = db.scalar(
        select(ArticleEditor).where(
            ArticleEditor.article_id == article_id,
            ArticleEditor.user_id == user_id,
        )
    )
    if existing:
        raise _ALREADY_ASSIGNED

    assignment = ArticleEditor(
        article_id=article_id,
        user_id=user_id,
        assigned_by=assigner_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def unassign_reviewer(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    assignment = db.scalar(
        select(ArticleReviewer).where(
            ArticleReviewer.article_id == article_id,
            ArticleReviewer.user_id == user_id,
        )
    )
    if not assignment:
        raise _ASSIGNMENT_NOT_FOUND
    db.delete(assignment)
    db.commit()


def unassign_editor(db: Session, article_id: uuid.UUID, user_id: uuid.UUID) -> None:
    assignment = db.scalar(
        select(ArticleEditor).where(
            ArticleEditor.article_id == article_id,
            ArticleEditor.user_id == user_id,
        )
    )
    if not assignment:
        raise _ASSIGNMENT_NOT_FOUND
    db.delete(assignment)
    db.commit()


def override_decision(
    db: Session, article_id: uuid.UUID, status: VersionStatus
) -> ArticleVersion:
    if status not in _OVERRIDE_ALLOWED:
        raise _INVALID_STATUS
    if not db.get(Article, article_id):
        raise _NOT_FOUND
    version = article_service.current_version(db, article_id)
    version.status = status
    if status == VersionStatus.SUBMITTED and version.submitted_at is None:
        version.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(version)
    return version
