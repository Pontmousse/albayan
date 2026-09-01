import uuid
from typing import Literal

from sqlalchemy.orm import Session

from app.models.enums import IssueCategory, IssueStatus, NotificationType
from app.models.issue import Issue
from app.services import issue_service, notification_copy, notification_service

IssueSort = Literal["date", "upvotes"]
SortDirection = Literal["asc", "desc"]


def list_issues(
    db: Session,
    *,
    status: IssueStatus | None = None,
    category: IssueCategory | None = None,
    sort: IssueSort = "date",
    direction: SortDirection = "desc",
) -> list[Issue]:
    return issue_service.list_issues(
        db,
        status=status,
        category=category,
        sort=sort,
        direction=direction,
    )


def update_issue_status(
    db: Session,
    *,
    issue_id: uuid.UUID,
    admin_id: uuid.UUID,
    status: IssueStatus,
) -> Issue:
    issue = issue_service.get_issue(db, issue_id)
    previous_status = issue.status
    if previous_status == status:
        return issue

    issue.status = status
    db.flush()
    notification_service.create_notification(
        db,
        user_id=issue.user_id,
        actor_id=admin_id,
        type=NotificationType.ISSUE_STATUS_CHANGED,
        title=notification_copy.issue_status_changed_title(status),
        body=notification_copy.issue_status_changed_body(issue.title, status),
        link=f"/balaghat?issue={issue.id}",
        metadata={
            "issue_id": str(issue.id),
            "previous_status": previous_status.value,
            "next_status": status.value,
        },
        event_key=f"issue:{issue.id}:status:{status.value}",
    )
    db.commit()
    return issue_service.get_issue(db, issue_id)
