import uuid
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import Article, ArticleEditor, ArticleReviewer, ArticleVersion, Review
from app.models.enums import (
    NotificationType,
    ReviewRecommendation,
    ReviewerAssignmentStatus,
    ReviewStatus,
)
from app.models.user import User
from app.services import article_service
from app.services import email_service, workflow_notification_service

logger = logging.getLogger(__name__)

_NOT_FOUND = HTTPException(status_code=404, detail="التعيين غير موجود.")
_FORBIDDEN = HTTPException(status_code=404, detail="التعيين غير موجود.")
_ALREADY_SUBMITTED = HTTPException(status_code=409, detail="تم تسليم هذه المراجعة بالفعل.")
_NEED_RECOMMENDATION = HTTPException(
    status_code=400, detail="يلزم اختيار توصية قبل التسليم."
)

_ACTIVE = {ReviewerAssignmentStatus.ACCEPTED, ReviewerAssignmentStatus.COMPLETED}


def assert_is_reviewer(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> ArticleReviewer:
    assignment = db.scalar(
        select(ArticleReviewer).where(
            ArticleReviewer.article_id == article_id,
            ArticleReviewer.user_id == user_id,
            ArticleReviewer.status.in_(_ACTIVE),
        )
    )
    if not assignment:
        raise _FORBIDDEN
    return assignment


def get_assignment_for_user(
    db: Session, assignment_id: uuid.UUID, user_id: uuid.UUID
) -> ArticleReviewer:
    assignment = db.scalar(
        select(ArticleReviewer)
        .where(ArticleReviewer.id == assignment_id)
        .options(
            selectinload(ArticleReviewer.article).selectinload(Article.versions),
            selectinload(ArticleReviewer.reviews),
        )
    )
    if (
        not assignment
        or assignment.user_id != user_id
        or assignment.status not in _ACTIVE
    ):
        raise _NOT_FOUND
    return assignment


def list_assignments_for_reviewer(
    db: Session, user_id: uuid.UUID
) -> list[ArticleReviewer]:
    return list(
        db.scalars(
            select(ArticleReviewer)
            .where(
                ArticleReviewer.user_id == user_id,
                ArticleReviewer.status.in_(_ACTIVE),
            )
            .options(
                selectinload(ArticleReviewer.article).selectinload(Article.versions),
                selectinload(ArticleReviewer.reviews),
            )
            .order_by(ArticleReviewer.invited_at.desc())
        ).all()
    )


def _review_for_current_version(
    assignment: ArticleReviewer, version: ArticleVersion
) -> Review | None:
    matches = [
        r for r in assignment.reviews if r.article_version_id == version.id
    ]
    if not matches:
        return None
    return max(matches, key=lambda r: r.created_at)


def upsert_draft_review(
    db: Session,
    assignment: ArticleReviewer,
    *,
    comments_to_author: str | None,
    comments_to_editor: str | None,
    recommendation: ReviewRecommendation | None,
) -> Review:
    if assignment.status == ReviewerAssignmentStatus.COMPLETED:
        raise _ALREADY_SUBMITTED

    version = article_service.current_version(db, assignment.article_id)
    review = _review_for_current_version(assignment, version)
    if review and review.status == ReviewStatus.SUBMITTED:
        raise _ALREADY_SUBMITTED

    if not review:
        review = Review(
            article_reviewer_id=assignment.id,
            article_version_id=version.id,
            status=ReviewStatus.DRAFT,
        )
        db.add(review)

    review.comments_to_author = comments_to_author
    review.comments_to_editor = comments_to_editor
    review.recommendation = recommendation
    review.status = ReviewStatus.DRAFT
    db.commit()
    db.refresh(review)
    return review


def submit_review(db: Session, assignment: ArticleReviewer) -> Review:
    if assignment.status == ReviewerAssignmentStatus.COMPLETED:
        raise _ALREADY_SUBMITTED

    version = article_service.current_version(db, assignment.article_id)
    review = _review_for_current_version(assignment, version)
    if not review:
        raise _NEED_RECOMMENDATION
    if review.status == ReviewStatus.SUBMITTED:
        raise _ALREADY_SUBMITTED
    if review.recommendation is None:
        raise _NEED_RECOMMENDATION

    now = datetime.now(timezone.utc)
    review.status = ReviewStatus.SUBMITTED
    review.submitted_at = now
    assignment.status = ReviewerAssignmentStatus.COMPLETED
    article = db.scalar(
        select(Article)
        .where(Article.id == assignment.article_id)
        .options(
            selectinload(Article.editor_assignments).selectinload(ArticleEditor.user),
        )
    )
    if article:
        editor_ids = {link.user_id for link in article.editor_assignments}
        admin_ids = workflow_notification_service.admin_ids(db)
        metadata = {
            "article_id": str(article.id),
            "review_id": str(review.id),
            "assignment_id": str(assignment.id),
        }
        workflow_notification_service.notify_many(
            db,
            user_ids=editor_ids,
            type=NotificationType.REVIEW_SUBMITTED,
            title="تم تسليم مراجعة جديدة",
            body=f"سُلّمت مراجعة جديدة للبحث «{article.title}».",
            link=f"/maktabi/tahriri/{article.id}",
            actor_id=assignment.user_id,
            event_scope=f"review:{review.id}:submitted:editor",
            metadata=metadata,
        )
        workflow_notification_service.notify_many(
            db,
            user_ids=admin_ids - editor_ids,
            type=NotificationType.REVIEW_SUBMITTED,
            title="تم تسليم مراجعة جديدة",
            body=f"سُلّمت مراجعة جديدة للبحث «{article.title}».",
            link=f"/admin/maqalat/{article.id}",
            actor_id=assignment.user_id,
            event_scope=f"review:{review.id}:submitted:admin",
            metadata=metadata,
        )
    db.commit()
    db.refresh(review)
    db.refresh(assignment)
    if article:
        reviewer = db.get(User, assignment.user_id)
        reviewer_name = (
            reviewer.full_name
            if reviewer and reviewer.full_name
            else reviewer.email
            if reviewer
            else "مراجع"
        )
        site_url = email_service.settings.frontend_base_url.rstrip("/")
        recipient_urls = {
            link.user.email.strip().lower(): f"{site_url}/maktabi/tahriri/{article.id}"
            for link in article.editor_assignments
        }
        for admin in db.scalars(select(User).where(User.is_admin.is_(True))).all():
            recipient_urls.setdefault(
                admin.email.strip().lower(),
                f"{site_url}/admin/maqalat/{article.id}",
            )
        for recipient, report_url in sorted(recipient_urls.items()):
            try:
                email_service.send_review_submitted_email(
                    to=recipient,
                    article_title=article.title,
                    reviewer_name=reviewer_name,
                    report_url=report_url,
                    idempotency_key=f"review-submitted/{review.id}/{recipient}",
                )
            except Exception as exc:
                logger.warning("Review submitted email failed for %s: %s", review.id, exc)
    return review
