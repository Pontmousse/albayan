import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.dates import format_date
from app.models.article import Article, ArticleReviewer
from app.models.email_digest_state import EmailDigestState
from app.models.enums import ReviewerAssignmentStatus
from app.models.notification import Notification
from app.models.user import User
from app.services import email_service

logger = logging.getLogger(__name__)

DIGEST_UNREAD_THRESHOLD = 5
DIGEST_COOLDOWN = timedelta(days=7)
DUE_SOON_WINDOW = timedelta(days=1)


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _review_url(assignment_id) -> str:
    return (
        f"{email_service.settings.frontend_base_url.rstrip('/')}"
        f"/maktabi/murajaati/{assignment_id}"
    )


def send_due_review_reminders(db: Session, *, now: datetime | None = None) -> int:
    """Send midpoint and due-soon reminders for accepted reviewer assignments.

    Intended to be called by a deployment cron/job runner. FastAPI does not start
    a hidden in-process scheduler, so multiple replicas do not duplicate work.
    """
    current = now or _now_utc()
    rows = list(
        db.scalars(
            select(ArticleReviewer)
            .where(ArticleReviewer.status == ReviewerAssignmentStatus.ACCEPTED)
            .where(ArticleReviewer.review_due_at.is_not(None))
            .options(
                selectinload(ArticleReviewer.article),
                selectinload(ArticleReviewer.user),
            )
        ).all()
    )

    sent = 0
    for assignment in rows:
        if not assignment.review_due_at:
            continue
        if assignment.review_due_at <= current:
            continue

        midpoint = assignment.invited_at + (
            (assignment.review_due_at - assignment.invited_at) / 2
        )
        reminder_kind: str | None = None
        reminder_text = ""
        if (
            assignment.reminder_midpoint_sent_at is None
            and current >= midpoint
            and current < assignment.review_due_at - DUE_SOON_WINDOW
        ):
            reminder_kind = "midpoint"
            reminder_text = "بلغت المراجعة منتصف المهلة المحددة."
        elif (
            assignment.reminder_due_soon_sent_at is None
            and current >= assignment.review_due_at - DUE_SOON_WINDOW
        ):
            reminder_kind = "due-soon"
            reminder_text = "تبقى يوم واحد تقريبًا على موعد تسليم المراجعة."

        if not reminder_kind:
            continue

        try:
            email_service.send_review_reminder_email(
                to=assignment.user.email,
                article_title=assignment.article.title,
                review_url=_review_url(assignment.id),
                due_text=format_date(assignment.review_due_at),
                reminder_text=reminder_text,
                idempotency_key=f"review-reminder/{assignment.id}/{reminder_kind}",
            )
        except Exception as exc:
            logger.warning("Review reminder email failed for %s: %s", assignment.id, exc)
            continue

        if reminder_kind == "midpoint":
            assignment.reminder_midpoint_sent_at = current
        else:
            assignment.reminder_due_soon_sent_at = current
        sent += 1

    if sent:
        db.commit()
    return sent


def send_unread_notification_digests(
    db: Session, *, now: datetime | None = None
) -> int:
    """Send weekly email nudges for users with more than five unread notifications."""
    current = now or _now_utc()
    unread_counts = (
        select(
            Notification.user_id.label("user_id"),
            func.count(Notification.id).label("unread_count"),
        )
        .where(Notification.is_read.is_(False))
        .group_by(Notification.user_id)
        .having(func.count(Notification.id) > DIGEST_UNREAD_THRESHOLD)
        .subquery()
    )
    rows = list(
        db.execute(
            select(User, unread_counts.c.unread_count)
            .join(unread_counts, unread_counts.c.user_id == User.id)
            .outerjoin(EmailDigestState, EmailDigestState.user_id == User.id)
            .where(
                (EmailDigestState.last_unread_digest_sent_at.is_(None))
                | (
                    EmailDigestState.last_unread_digest_sent_at
                    <= current - DIGEST_COOLDOWN
                )
            )
        ).all()
    )

    sent = 0
    notifications_url = (
        f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/isharat"
    )
    for user, unread_count in rows:
        try:
            email_service.send_unread_notifications_digest_email(
                to=user.email,
                unread_count=int(unread_count),
                notifications_url=notifications_url,
            )
        except Exception as exc:
            logger.warning("Unread digest email failed for user %s: %s", user.id, exc)
            continue

        state = db.get(EmailDigestState, user.id)
        if state is None:
            state = EmailDigestState(user_id=user.id)
            db.add(state)
        state.last_unread_digest_sent_at = current
        sent += 1

    if sent:
        db.commit()
    return sent
