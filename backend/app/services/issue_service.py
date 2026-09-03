import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import s3
from app.models.enums import IssueCategory, IssueStatus, NotificationType
from app.models.issue import Issue, IssueImage, IssueUpvote
from app.services import notification_service, workflow_notification_service

ISSUE_CREATE_LIMIT = 5
MAX_ISSUE_IMAGES = 3
MAX_ISSUE_IMAGE_BYTES = 5 * 1024 * 1024
IssueSort = Literal["date", "upvotes"]
SortDirection = Literal["asc", "desc"]

_NOT_FOUND = HTTPException(status_code=404, detail="البلاغ غير موجود.")
_IMAGE_NOT_FOUND = HTTPException(status_code=404, detail="الصورة غير موجودة.")
_REPORTER_ONLY = HTTPException(
    status_code=403,
    detail="يمكن لصاحب البلاغ فقط تعديل صوره.",
)
_RATE_LIMITED = HTTPException(
    status_code=429,
    detail="بلغت الحد الأقصى لإرسال البلاغات خلال 24 ساعة. جرّب لاحقاً.",
)
_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

logger = logging.getLogger(__name__)


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


def _add_issue(
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
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        status=IssueStatus.OPEN,
        upvote_count=0,
    )
    db.add(issue)
    db.flush()
    return issue


def _notify_issue_created(db: Session, issue: Issue) -> None:
    workflow_notification_service.notify_many(
        db,
        user_ids=workflow_notification_service.admin_ids(db),
        type=NotificationType.ISSUE_CREATED,
        title="بلاغ جديد",
        body=f"أُرسل بلاغ جديد بعنوان «{issue.title}».",
        link="/admin/balaghat",
        actor_id=issue.user_id,
        event_scope=f"issue:{issue.id}:created",
        metadata={"issue_id": str(issue.id), "category": issue.category.value},
    )


def create_issue(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str,
    category: IssueCategory,
) -> Issue:
    issue = _add_issue(
        db,
        user_id=user_id,
        title=title,
        description=description,
        category=category,
    )
    _notify_issue_created(db, issue)
    db.commit()
    db.refresh(issue)
    return issue


def _validated_image(body: bytes, content_type: str) -> tuple[str, str]:
    normalized_type = content_type.split(";")[0].strip().lower()
    ext = _ALLOWED_IMAGE_TYPES.get(normalized_type)
    if ext is None:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مدعوم. استخدم JPEG أو PNG أو GIF أو WebP.",
        )
    if not body:
        raise HTTPException(status_code=400, detail="الملف فارغ.")
    if len(body) > MAX_ISSUE_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="حجم الصورة يتجاوز الحد المسموح (5 ميغابايت).",
        )
    return normalized_type, ext


def _cleanup_uploaded_issue_images(keys: list[str]) -> None:
    for key in keys:
        try:
            s3.delete_key(key)
        except Exception:
            logger.exception("تعذّر تنظيف صورة بلاغ بعد فشل الإنشاء: %s", key)


def create_issue_with_images(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str,
    category: IssueCategory,
    images: list[tuple[bytes, str]],
) -> Issue:
    if len(images) > MAX_ISSUE_IMAGES:
        raise HTTPException(
            status_code=400,
            detail="يمكن إرفاق ثلاث صور كحد أقصى لكل بلاغ.",
        )

    validated_images = [
        (body, *_validated_image(body, content_type))
        for body, content_type in images
    ]
    uploaded_keys: list[str] = []

    try:
        issue = _add_issue(
            db,
            user_id=user_id,
            title=title,
            description=description,
            category=category,
        )
        storage_prefix = f"issues/{issue.id}/images"
        for position, (body, normalized_type, ext) in enumerate(validated_images):
            filename = f"{uuid.uuid4().hex}{ext}"
            s3_key = f"{storage_prefix}/{filename}"
            s3.put_bytes(storage_prefix, filename, body, normalized_type)
            uploaded_keys.append(s3_key)
            db.add(
                IssueImage(
                    issue_id=issue.id,
                    s3_key=s3_key,
                    position=position,
                )
            )

        db.flush()
        _notify_issue_created(db, issue)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            logger.exception("تعذّر التراجع عن معاملة إنشاء البلاغ")
        _cleanup_uploaded_issue_images(uploaded_keys)
        raise

    return get_issue(db, issue.id)


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
            link=f"/balaghat?issue={issue.id}",
            metadata={
                "issue_id": str(issue.id),
                "upvote_count": upvote_count,
            },
            event_key=f"issue:{issue.id}:upvote:{user_id}",
        )
        db.commit()
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


def _assert_reporter(issue: Issue, user_id: uuid.UUID) -> None:
    if issue.user_id != user_id:
        raise _REPORTER_ONLY


def create_issue_image(
    db: Session,
    *,
    issue_id: uuid.UUID,
    user_id: uuid.UUID,
    body: bytes,
    content_type: str,
) -> Issue:
    issue = get_issue(db, issue_id)
    _assert_reporter(issue, user_id)

    normalized_type, ext = _validated_image(body, content_type)

    image_count = int(
        db.scalar(
            select(func.count())
            .select_from(IssueImage)
            .where(IssueImage.issue_id == issue_id)
        )
        or 0
    )
    if image_count >= MAX_ISSUE_IMAGES:
        raise HTTPException(
            status_code=400,
            detail="يمكن إرفاق ثلاث صور كحد أقصى لكل بلاغ.",
        )

    max_position = db.scalar(
        select(func.max(IssueImage.position)).where(IssueImage.issue_id == issue_id)
    )
    position = 0 if max_position is None else int(max_position) + 1
    filename = f"{uuid.uuid4().hex}{ext}"
    storage_prefix = f"issues/{issue_id}/images"
    s3_key = f"{storage_prefix}/{filename}"
    s3.put_bytes(storage_prefix, filename, body, normalized_type)

    image = IssueImage(issue_id=issue_id, s3_key=s3_key, position=position)
    db.add(image)
    db.commit()
    return get_issue(db, issue_id)


def get_issue_image(db: Session, issue_id: uuid.UUID, image_id: uuid.UUID) -> IssueImage:
    get_issue(db, issue_id)
    image = db.scalar(
        select(IssueImage).where(
            IssueImage.id == image_id,
            IssueImage.issue_id == issue_id,
        )
    )
    if not image:
        raise _IMAGE_NOT_FOUND
    return image


def delete_issue_image(
    db: Session, issue_id: uuid.UUID, image_id: uuid.UUID, user_id: uuid.UUID
) -> Issue:
    issue = get_issue(db, issue_id)
    _assert_reporter(issue, user_id)
    image = db.scalar(
        select(IssueImage).where(
            IssueImage.id == image_id,
            IssueImage.issue_id == issue_id,
        )
    )
    if not image:
        raise _IMAGE_NOT_FOUND

    s3.delete_key(image.s3_key)
    db.delete(image)
    db.commit()
    return get_issue(db, issue_id)
