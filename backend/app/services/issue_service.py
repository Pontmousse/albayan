import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.enums import IssueCategory, IssueStatus, NotificationType
from app.models.issue import Issue, IssueUpvote
from app.services import notification_service

ISSUE_CREATE_LIMIT = 5
IssueSort = Literal["date", "upvotes"]
SortDirection = Literal["asc", "desc"]

_NOT_FOUND = HTTPException(status_code=404, detail="البلاغ غير موجود.")
_RATE_LIMITED = HTTPException(
    status_code=429,
    detail="بلغت الحد الأقصى لإرسال البلاغات خلال 24 ساعة. جرّب لاحقاً.",
)


def _recent_issue_count(db: Session, user_id: uuid.UUID) -> int:
    threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    return int(
        db.scalar(
            select(func.count())
            .select_from(Issue)
            .where(Issue.user_id == user_id, Issue.created_at > threshold)
        )
        or 0
    )


def create_issue(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str,
    category: IssueCategory,
) -> Issue:
    if _recent_issue_count(db, user_id) >= ISSUE_CREATE_LIMIT:
        raise _RATE_LIMITED

    issue = Issue(
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        status=IssueStatus.OPEN,
        upvote_count=0,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


def list_issues(
    db: Session,
    *,
    status: IssueStatus | None = None,
    category: IssueCategory | None = None,
    sort: IssueSort = "date",
    direction: SortDirection = "desc",
) -> list[Issue]:
    statement = select(Issue).options(
        selectinload(Issue.reporter), selectinload(Issue.images)
    )
    if status is not None:
        statement = statement.where(Issue.status == status)
    if category is not None:
        statement = statement.where(Issue.category == category)

    sort_column = Issue.upvote_count if sort == "upvotes" else Issue.created_at
    order_expression = sort_column.asc() if direction == "asc" else sort_column.desc()
    statement = statement.order_by(order_expression, Issue.created_at.desc())

    return list(
        db.scalars(statement)
        .unique()
        .all()
    )


def get_issue(db: Session, issue_id: uuid.UUID) -> Issue:
    issue = db.scalar(
        select(Issue)
        .where(Issue.id == issue_id)
        .options(selectinload(Issue.reporter), selectinload(Issue.images))
    )
    if not issue:
        raise _NOT_FOUND
    return issue


def upvoted_issue_ids(
    db: Session, user_id: uuid.UUID, issue_ids: list[uuid.UUID]
) -> set[uuid.UUID]:
    if not issue_ids:
        return set()

    return set(
        db.scalars(
            select(IssueUpvote.issue_id).where(
                IssueUpvote.user_id == user_id,
                IssueUpvote.issue_id.in_(issue_ids),
            )
        ).all()
    )


def has_upvoted(db: Session, user_id: uuid.UUID, issue_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(IssueUpvote.issue_id).where(
                IssueUpvote.user_id == user_id,
                IssueUpvote.issue_id == issue_id,
            )
        )
        is not None
    )


def upvote_issue(db: Session, issue_id: uuid.UUID, user_id: uuid.UUID) -> Issue:
    issue = get_issue(db, issue_id)
    upvote = IssueUpvote(issue_id=issue_id, user_id=user_id)
    db.add(upvote)

    created = False
    try:
        db.flush()
        db.execute(
            update(Issue)
            .where(Issue.id == issue_id)
            .values(upvote_count=Issue.upvote_count + 1)
        )
        created = True
    except IntegrityError:
        db.rollback()
        return get_issue(db, issue_id)

    upvote_count = int(
        db.scalar(select(Issue.upvote_count).where(Issue.id == issue_id)) or 0
    )
    if created and issue.user_id != user_id:
        notification_service.create_notification(
            db,
            user_id=issue.user_id,
            actor_id=user_id,
            type=NotificationType.ISSUE_UPVOTED,
            title="صوّت مستخدم على بلاغك",
            body=f"حصل البلاغ «{issue.title}» على تصويت جديد.",
            link=f"/maktabi/balaghat?issue={issue.id}",
            metadata={
                "issue_id": str(issue.id),
                "upvote_count": upvote_count,
            },
        )
    else:
        db.commit()

    return get_issue(db, issue_id)


def remove_upvote(db: Session, issue_id: uuid.UUID, user_id: uuid.UUID) -> Issue:
    issue = get_issue(db, issue_id)
    result = db.execute(
        delete(IssueUpvote).where(
            IssueUpvote.issue_id == issue_id,
            IssueUpvote.user_id == user_id,
        )
    )
    if result.rowcount:
        db.execute(
            update(Issue)
            .where(Issue.id == issue_id)
            .values(
                upvote_count=case(
                    (Issue.upvote_count > 0, Issue.upvote_count - 1),
                    else_=0,
                )
            )
        )
    db.commit()
    return get_issue(db, issue_id)
