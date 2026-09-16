import uuid
from datetime import datetime, timezone
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleEditor,
    ArticleReviewer,
    ArticleVersion,
    Review,
)
from app.models.enums import ArticleStatus, NotificationType, ReviewerAssignmentStatus
from app.models.user import User
from app.core.dates import format_date
from app.services import article_service, email_service, workflow_notification_service

logger = logging.getLogger(__name__)

_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_USER_NOT_FOUND = HTTPException(status_code=404, detail="المستخدم غير موجود.")
_ALREADY_ASSIGNED = HTTPException(status_code=409, detail="المستخدم معيّن بالفعل على هذا المقال.")
_ASSIGNMENT_NOT_FOUND = HTTPException(status_code=404, detail="التعيين غير موجود.")
_NO_FORMAL_VERSION = HTTPException(
    status_code=409, detail="لا يمكن التعيين قبل تقديم المقال."
)
_ROUND_NOT_OPEN = HTTPException(
    status_code=409, detail="يمكن تعيين المراجعين لأحدث جولة مفتوحة فقط."
)
_INVALID_STATUS = HTTPException(
    status_code=400,
    detail="حالة الإصدار غير صالحة للتجاوز.",
)

_OVERRIDE_ALLOWED = {
    ArticleStatus.SUBMITTED,
    ArticleStatus.UNDER_REVIEW,
    ArticleStatus.REVISION_REQUESTED,
    ArticleStatus.ACCEPTED,
    ArticleStatus.REJECTED,
    ArticleStatus.PUBLISHED,
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
            selectinload(Article.reviewer_assignments).selectinload(
                ArticleReviewer.reviews
            ),
            selectinload(Article.editor_assignments).selectinload(ArticleEditor.user),
        )
    )
    if not article:
        raise _NOT_FOUND
    return article


def list_articles(
    db: Session, status: ArticleStatus | None = None
) -> list[tuple[Article, ArticleVersion | None]]:
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
    result: list[tuple[Article, ArticleVersion | None]] = []
    for article in articles:
        latest = max(article.versions, key=lambda v: v.version_number) if article.versions else None
        if status is not None and article.status != status:
            continue
        result.append((article, latest))
    return result


def assign_reviewer(
    db: Session,
    article_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    assigner_id: uuid.UUID | None = None,
    review_due_at: datetime | None = None,
) -> ArticleReviewer:
    article = db.get(Article, article_id)
    if not article:
        raise _NOT_FOUND
    if user_id is None:
        raise HTTPException(status_code=400, detail="يلزم تحديد user_id.")
    if (
        review_due_at is None
        or review_due_at.tzinfo is None
        or review_due_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=422,
            detail="يلزم تحديد موعد مستقبلي لتسليم المراجعة.",
        )
    version = article_service.latest_version(db, article_id)
    if version is None:
        raise _NO_FORMAL_VERSION
    if article.status not in {ArticleStatus.SUBMITTED, ArticleStatus.UNDER_REVIEW}:
        raise _ROUND_NOT_OPEN

    user = db.get(User, user_id)
    if not user:
        raise _USER_NOT_FOUND

    existing = db.scalar(
        select(ArticleReviewer).where(
            ArticleReviewer.article_version_id == version.id,
            ArticleReviewer.user_id == user_id,
        )
    )
    if existing:
        raise _ALREADY_ASSIGNED

    now = datetime.now(timezone.utc)
    assignment = ArticleReviewer(
        article_id=article_id,
        article_version_id=version.id,
        user_id=user_id,
        status=ReviewerAssignmentStatus.ACCEPTED,
        invited_at=now,
        review_due_at=review_due_at,
        accepted_at=now,
    )
    db.add(assignment)
    db.flush()
    workflow_notification_service.notify_many(
        db,
        user_ids={user.id},
        type=NotificationType.REVIEWER_ASSIGNED,
        title="مهمة مراجعة جديدة",
        body=f"عُيّنت لمراجعة البحث «{version.title_snapshot}».",
        link=f"/maktabi/murajaati/{assignment.id}",
        actor_id=assigner_id,
        event_scope=f"article:{article.id}:reviewer-assignment:{assignment.id}",
        metadata={"article_id": str(article.id), "assignment_id": str(assignment.id)},
    )
    db.commit()
    db.refresh(assignment)
    try:
        email_service.send_reviewer_assigned_email(
            to=user.email,
            article_title=version.title_snapshot,
            review_url=f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/murajaati/{assignment.id}",
            due_text=format_date(review_due_at) if review_due_at else "",
            idempotency_key=f"reviewer-assigned/{assignment.id}",
        )
    except Exception as exc:
        logger.warning("Reviewer assignment email failed for %s: %s", assignment.id, exc)
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
    if article.status == ArticleStatus.DRAFT or article_service.latest_version(db, article_id) is None:
        raise _NO_FORMAL_VERSION
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
    db.flush()
    workflow_notification_service.notify_many(
        db,
        user_ids={user.id},
        type=NotificationType.EDITOR_ASSIGNED,
        title="تعيين تحريري جديد",
        body=f"عُيّنت محررًا على البحث «{article.title}».",
        link=f"/maktabi/tahriri/{article.id}",
        actor_id=assigner_id,
        event_scope=f"article:{article.id}:editor-assignment:{assignment.id}",
        metadata={"article_id": str(article.id), "assignment_id": str(assignment.id)},
    )
    db.commit()
    db.refresh(assignment)
    try:
        email_service.send_editor_assigned_email(
            to=user.email,
            article_title=article.title,
            article_url=f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/tahriri/{article.id}",
            idempotency_key=f"editor-assigned/{assignment.id}",
        )
    except Exception as exc:
        logger.warning("Editor assignment email failed for %s: %s", assignment.id, exc)
    return assignment


def unassign_reviewer(
    db: Session,
    article_id: uuid.UUID,
    assignment_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
) -> None:
    assignment = db.get(ArticleReviewer, assignment_id)
    if not assignment or assignment.article_id != article_id:
        raise _ASSIGNMENT_NOT_FOUND
    article = db.get(Article, article_id)
    latest = article_service.latest_version(db, article_id)
    has_report = db.scalar(
        select(Review.id).where(Review.article_reviewer_id == assignment.id).limit(1)
    )
    if (
        article is None
        or latest is None
        or assignment.article_version_id != latest.id
        or article.status not in {ArticleStatus.SUBMITTED, ArticleStatus.UNDER_REVIEW}
        or has_report is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="لا يمكن حذف تعيين من جولة مغلقة أو بعد بدء التقرير.",
        )
    workflow_notification_service.notify_many(
        db,
        user_ids={assignment.user_id},
        type=NotificationType.ASSIGNMENT_REMOVED,
        title="أُلغي تكليف المراجعة",
        body=f"أُلغي تكليفك بمراجعة البحث «{article.title if article else 'بحث'}».",
        link="/maktabi/murajaati",
        actor_id=actor_id,
        event_scope=f"article:{article_id}:reviewer-assignment:{assignment.id}:removed",
        metadata={"article_id": str(article_id), "assignment_id": str(assignment.id)},
    )
    db.delete(assignment)
    db.commit()


def unassign_editor(
    db: Session,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
) -> None:
    assignment = db.scalar(
        select(ArticleEditor).where(
            ArticleEditor.article_id == article_id,
            ArticleEditor.user_id == user_id,
        )
    )
    if not assignment:
        raise _ASSIGNMENT_NOT_FOUND
    article = db.get(Article, article_id)
    workflow_notification_service.notify_many(
        db,
        user_ids={user_id},
        type=NotificationType.ASSIGNMENT_REMOVED,
        title="أُلغي التكليف التحريري",
        body=f"أُلغي تكليفك بتحرير البحث «{article.title if article else 'بحث'}».",
        link="/maktabi/tahriri",
        actor_id=actor_id,
        event_scope=f"article:{article_id}:editor-assignment:{assignment.id}:removed",
        metadata={"article_id": str(article_id), "assignment_id": str(assignment.id)},
    )
    db.delete(assignment)
    db.commit()


def override_decision(
    db: Session,
    article_id: uuid.UUID,
    status: ArticleStatus,
    *,
    actor_id: uuid.UUID | None = None,
    reason: str | None = None,
    disclosures: list[object] | None = None,
) -> ArticleVersion:
    if status not in _OVERRIDE_ALLOWED:
        raise _INVALID_STATUS
    if status == ArticleStatus.REVISION_REQUESTED:
        if actor_id is None:
            raise HTTPException(status_code=403, detail="تعذّر تحديد مصدر قرار التعديل.")
        from app.services import editor_service

        return editor_service.request_revisions(
            db,
            article_id,
            actor_id,
            reason or "",
            disclosures,
            require_editor=False,
        )
    article = db.get(Article, article_id)
    if not article:
        raise _NOT_FOUND
    version = article_service.latest_version(db, article_id)
    if version is None:
        raise HTTPException(status_code=409, detail="لا يوجد إصدار رسمي للمقال.")
    if article.status == status:
        return version
    transition_marker = datetime.now(timezone.utc).isoformat()
    article.status = status
    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.author_links).selectinload(ArticleAuthor.user))
    )
    if article:
        author_ids = workflow_notification_service.author_ids(article)
        type = (
            NotificationType.ARTICLE_PUBLISHED
            if status == ArticleStatus.PUBLISHED
            else NotificationType.EDITORIAL_DECISION
        )
        label = {
            ArticleStatus.SUBMITTED: "مُقدَّم",
            ArticleStatus.UNDER_REVIEW: "قيد المراجعة",
            ArticleStatus.ACCEPTED: "مقبول",
            ArticleStatus.REJECTED: "مرفوض",
            ArticleStatus.PUBLISHED: "منشور",
        }[status]
        workflow_notification_service.notify_many(
            db,
            user_ids=author_ids,
            type=type,
            title="نُشر بحثك" if status == ArticleStatus.PUBLISHED else "قرار تحريري جديد",
            body=f"أصبحت حالة البحث «{version.title_snapshot}»: {label}.",
            link=f"/maktabi/maqalati/{article.id}",
            actor_id=actor_id,
            event_scope=(
                f"article:{article.id}:version:{version.version_number}:"
                f"status:{status.value}:{transition_marker}"
            ),
            metadata={
                "article_id": str(article.id),
                "version_number": version.version_number,
                "status": status.value,
            },
        )
    db.commit()
    db.refresh(version)
    if article and status == ArticleStatus.PUBLISHED:
        article_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/maqalati/{article.id}"
        for link in article.author_links:
            try:
                email_service.send_article_published_email(
                    to=link.user.email,
                    article_title=version.title_snapshot,
                    article_url=article_url,
                    idempotency_key=(
                        f"article-published/{article.id}/{version.version_number}/"
                        f"{transition_marker}/{link.user_id}"
                    ),
                )
            except Exception as exc:
                logger.warning("Article published email failed for %s: %s", article.id, exc)
    elif article and status in {
        ArticleStatus.UNDER_REVIEW,
        ArticleStatus.ACCEPTED,
        ArticleStatus.REJECTED,
    }:
        article_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/maqalati/{article.id}"
        label = {
            ArticleStatus.UNDER_REVIEW: "قيد المراجعة",
            ArticleStatus.ACCEPTED: "قبول",
            ArticleStatus.REJECTED: "رفض",
        }[status]
        next_step = {
            ArticleStatus.UNDER_REVIEW: "سنوافيكم بأي مستجدات بعد اكتمال أعمال التحكيم.",
            ArticleStatus.ACCEPTED: "يرجى متابعة لوحة المقال لأي تعليمات نهائية قبل النشر.",
            ArticleStatus.REJECTED: "يمكنكم مراجعة القرار والتواصل مع هيئة التحرير عند الحاجة.",
        }[status]
        for link in article.author_links:
            try:
                email_service.send_decision_email(
                    to=link.user.email,
                    article_title=version.title_snapshot,
                    decision_text=label,
                    article_url=article_url,
                    next_step=next_step,
                    idempotency_key=(
                        f"decision/{article.id}/{version.version_number}/{status.value}/"
                        f"{transition_marker}/{link.user_id}"
                    ),
                )
            except Exception as exc:
                logger.warning("Decision email failed for article %s: %s", article.id, exc)
    return version
