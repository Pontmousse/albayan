import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.article import Article, ArticleEditor, ArticleReviewer
from app.models.enums import (
    InvitationRole,
    InvitationStatus,
    NotificationType,
    ReviewerAssignmentStatus,
)
from app.models.invitation import Invitation
from app.models.user import User
from app.core.dates import format_date
from app.services import workflow_notification_service
from app.services.email_service import send_invitation_email

_NOT_FOUND = HTTPException(status_code=404, detail="الدعوة غير موجودة.")
_ARTICLE_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_DUPLICATE = HTTPException(
    status_code=409,
    detail="توجد دعوة معلّقة بالفعل لهذا البريد والدور على المقال.",
)
_INVALID = HTTPException(status_code=400, detail="لا يمكن قبول هذه الدعوة.")
_EMAIL_MISMATCH = HTTPException(
    status_code=403,
    detail="البريد المستخدم لا يطابق بريد الدعوة.",
)

_INVITE_DAYS = 7


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def create_invitation(
    db: Session,
    *,
    article_id: uuid.UUID,
    role: InvitationRole,
    email: str,
    invited_by: uuid.UUID,
    send_email: bool = True,
    review_due_at: datetime | None = None,
) -> tuple[Invitation, str | None]:
    """ينشئ دعوة. يعيد (invitation, warning) — warning عند فشل البريد بعد الحفظ."""
    article = db.get(Article, article_id)
    if not article:
        raise _ARTICLE_NOT_FOUND
    if role == InvitationRole.REVIEWER and (
        review_due_at is None
        or review_due_at.tzinfo is None
        or review_due_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=422,
            detail="يلزم تحديد موعد مستقبلي لتسليم المراجعة.",
        )

    email_norm = _normalize_email(email)
    existing = db.scalar(
        select(Invitation).where(
            Invitation.article_id == article_id,
            Invitation.email == email_norm,
            Invitation.role == role,
            Invitation.status == InvitationStatus.PENDING,
        )
    )
    if existing:
        raise _DUPLICATE

    now = datetime.now(timezone.utc)
    invitation = Invitation(
        article_id=article_id,
        role=role,
        email=email_norm,
        token=secrets.token_urlsafe(32),
        status=InvitationStatus.PENDING,
        invited_by=invited_by,
        expires_at=now + timedelta(days=_INVITE_DAYS),
        review_due_at=review_due_at if role == InvitationRole.REVIEWER else None,
    )
    db.add(invitation)
    db.flush()
    existing_user = db.scalar(
        select(User).where(func.lower(User.email) == email_norm)
    )
    if existing_user:
        role_label = "مراجع" if role == InvitationRole.REVIEWER else "محرر"
        workflow_notification_service.notify_many(
            db,
            user_ids={existing_user.id},
            type=NotificationType.ARTICLE_INVITATION,
            title="دعوة للمشاركة في بحث",
            body=f"دُعيت للمشاركة بصفة {role_label} في البحث «{article.title}».",
            link=f"/daawa/{invitation.token}",
            actor_id=invited_by,
            event_scope=f"article-invitation:{invitation.id}:created",
            metadata={
                "article_id": str(article.id),
                "invitation_id": str(invitation.id),
                "role": role.value,
            },
        )
    db.commit()
    db.refresh(invitation)

    warning: str | None = None
    if send_email:
        try:
            send_invitation_email(
                to=email_norm,
                article_title=article.title,
                role=role,
                token=invitation.token,
                expires_at=invitation.expires_at,
                review_due_text=format_date(invitation.review_due_at)
                if invitation.review_due_at
                else "",
            )
        except HTTPException as exc:
            warning = exc.detail if isinstance(exc.detail, str) else "تعذّر إرسال البريد."

    return invitation, warning


def list_invitations(db: Session, article_id: uuid.UUID) -> list[Invitation]:
    if not db.get(Article, article_id):
        raise _ARTICLE_NOT_FOUND
    return list(
        db.scalars(
            select(Invitation)
            .where(Invitation.article_id == article_id)
            .order_by(Invitation.created_at.desc())
        ).all()
    )


def get_invitation(db: Session, invitation_id: uuid.UUID) -> Invitation:
    invitation = db.get(Invitation, invitation_id)
    if not invitation:
        raise _NOT_FOUND
    return invitation


def resend_invitation(db: Session, invitation_id: uuid.UUID) -> Invitation:
    invitation = get_invitation(db, invitation_id)
    now = datetime.now(timezone.utc)
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=409, detail="لا يمكن إعادة إرسال دعوة غير معلّقة.")
    if invitation.expires_at <= now:
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=410, detail="انتهت صلاحية الدعوة.")

    article = db.get(Article, invitation.article_id)
    if not article:
        raise _ARTICLE_NOT_FOUND

    send_invitation_email(
        to=invitation.email,
        article_title=article.title,
        role=invitation.role,
        token=invitation.token,
        expires_at=invitation.expires_at,
        review_due_text=format_date(invitation.review_due_at)
        if invitation.review_due_at
        else "",
    )
    return invitation


def cancel_invitation(db: Session, invitation_id: uuid.UUID) -> None:
    invitation = get_invitation(db, invitation_id)
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=409, detail="لا يمكن إلغاء دعوة غير معلّقة.")
    invitation.status = InvitationStatus.CANCELLED
    db.commit()


def accept_invitation(
    db: Session, *, token: str, user: User
) -> Invitation:
    invitation = db.scalar(
        select(Invitation)
        .where(Invitation.token == token)
        .options(selectinload(Invitation.article))
    )
    if not invitation:
        raise _NOT_FOUND

    now = datetime.now(timezone.utc)
    if invitation.status == InvitationStatus.CANCELLED:
        raise _INVALID
    if invitation.status == InvitationStatus.ACCEPTED:
        raise HTTPException(status_code=409, detail="تم قبول هذه الدعوة مسبقاً.")
    if invitation.expires_at <= now or invitation.status == InvitationStatus.EXPIRED:
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=410, detail="انتهت صلاحية الدعوة.")

    if _normalize_email(user.email) != _normalize_email(invitation.email):
        raise _EMAIL_MISMATCH

    assignment_id: uuid.UUID | None = None
    if invitation.role == InvitationRole.REVIEWER:
        existing = db.scalar(
            select(ArticleReviewer).where(
                ArticleReviewer.article_id == invitation.article_id,
                ArticleReviewer.user_id == user.id,
            )
        )
        if not existing:
            assignment = ArticleReviewer(
                article_id=invitation.article_id,
                user_id=user.id,
                status=ReviewerAssignmentStatus.ACCEPTED,
                invited_at=invitation.created_at,
                review_due_at=invitation.review_due_at,
                accepted_at=now,
            )
            db.add(assignment)
            db.flush()
            assignment_id = assignment.id
        elif existing.status == ReviewerAssignmentStatus.INVITED:
            existing.status = ReviewerAssignmentStatus.ACCEPTED
            existing.review_due_at = invitation.review_due_at
            existing.accepted_at = now
            assignment_id = existing.id
        else:
            assignment_id = existing.id
    else:
        existing_editor = db.scalar(
            select(ArticleEditor).where(
                ArticleEditor.article_id == invitation.article_id,
                ArticleEditor.user_id == user.id,
            )
        )
        if not existing_editor:
            editor_assignment = ArticleEditor(
                    article_id=invitation.article_id,
                    user_id=user.id,
                    assigned_by=invitation.invited_by,
                )
            db.add(editor_assignment)
            db.flush()
            assignment_id = editor_assignment.id
        else:
            assignment_id = existing_editor.id

    invitation.status = InvitationStatus.ACCEPTED
    role_label = "مراجع" if invitation.role == InvitationRole.REVIEWER else "محرر"
    destination = (
        f"/maktabi/murajaati/{assignment_id}"
        if invitation.role == InvitationRole.REVIEWER
        else f"/maktabi/tahriri/{invitation.article_id}"
    )
    workflow_notification_service.notify_many(
        db,
        user_ids={user.id},
        type=(
            NotificationType.REVIEWER_ASSIGNED
            if invitation.role == InvitationRole.REVIEWER
            else NotificationType.EDITOR_ASSIGNED
        ),
        title="أصبحت المهمة متاحة في مكتبك",
        body=f"قُبلت دعوتك بصفتك {role_label} للبحث «{invitation.article.title}».",
        link=destination,
        actor_id=invitation.invited_by,
        event_scope=f"article-invitation:{invitation.id}:accepted:assignee",
        metadata={
            "article_id": str(invitation.article_id),
            "invitation_id": str(invitation.id),
            "role": invitation.role.value,
        },
    )
    workflow_notification_service.notify_many(
        db,
        user_ids={invitation.invited_by},
        type=NotificationType.INVITATION_ACCEPTED,
        title="قُبلت دعوة المشاركة",
        body=f"قبل {user.full_name or user.email} دعوة المشاركة بصفة {role_label} في «{invitation.article.title}».",
        link=f"/admin/maqalat/{invitation.article_id}",
        actor_id=user.id,
        event_scope=f"article-invitation:{invitation.id}:accepted:inviter",
        metadata={
            "article_id": str(invitation.article_id),
            "invitation_id": str(invitation.id),
            "role": invitation.role.value,
        },
    )
    db.commit()
    db.refresh(invitation)
    return invitation
