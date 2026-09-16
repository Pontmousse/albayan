import uuid
import logging
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
    Review,
)
from app.core import s3
from app.core.actor import Actor
from app.models.article import ArticleDraftRevision
from app.models.enums import (
    ArticleStatus,
    DraftActorType,
    DraftRevisionReason,
    NotificationType,
    ReviewStatus,
)
from app.services import (
    article_draft_service,
    article_service,
    butex_worker_client,
    compile_service,
    email_service,
    workflow_notification_service,
)

_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_INVALID_STATUS = HTTPException(
    status_code=400, detail="حالة الإصدار غير صالحة لهذا القرار."
)
_DRAFT_BLOCKED = HTTPException(
    status_code=400,
    detail="لا يمكن اتخاذ قرار تحريري على مسودة — يجب تقديم المقال أولاً.",
)

_DECISION_ALLOWED = {
    ArticleStatus.UNDER_REVIEW,
    ArticleStatus.REVISION_REQUESTED,
    ArticleStatus.ACCEPTED,
    ArticleStatus.REJECTED,
}

_STATUS_AR = {
    ArticleStatus.UNDER_REVIEW: "قيد المراجعة",
    ArticleStatus.REVISION_REQUESTED: "مطلوب تعديل",
    ArticleStatus.ACCEPTED: "قبول",
    ArticleStatus.REJECTED: "رفض",
}

logger = logging.getLogger(__name__)

_EDITOR_TRANSITIONS = {
    ArticleStatus.SUBMITTED: _DECISION_ALLOWED,
    ArticleStatus.UNDER_REVIEW: {
        ArticleStatus.REVISION_REQUESTED,
        ArticleStatus.ACCEPTED,
        ArticleStatus.REJECTED,
    },
}


def _disclosure_map(
    reviews: list[Review], disclosures: list[object] | None
) -> dict[uuid.UUID, bool]:
    submitted_ids = {review.id for review in reviews if review.status == ReviewStatus.SUBMITTED}
    result: dict[uuid.UUID, bool] = {}
    for item in disclosures or []:
        review_id = getattr(item, "review_id", None)
        reveal = getattr(item, "reveal_identity", False)
        if not isinstance(review_id, uuid.UUID) or review_id not in submitted_ids:
            raise HTTPException(
                status_code=422,
                detail="إحدى خيارات كشف هوية المراجع غير صالحة.",
            )
        if review_id in result:
            raise HTTPException(status_code=422, detail="تكرر اختيار المراجع.")
        result[review_id] = bool(reveal)
    return result


def request_revisions(
    db: Session,
    article_id: uuid.UUID,
    actor_id: uuid.UUID,
    note: str,
    disclosures: list[object] | None = None,
    *,
    require_editor: bool = True,
) -> ArticleVersion:
    """Open one editable round from the exact latest immutable formal version."""
    if require_editor:
        assert_is_editor(db, article_id, actor_id)
    normalized_note = note.strip()
    if not normalized_note:
        raise HTTPException(status_code=422, detail="يلزم كتابة توجيهات التعديل.")

    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.author_links).selectinload(ArticleAuthor.user))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if article is None:
        raise _NOT_FOUND
    version = article_service.latest_version(db, article_id)
    if version is None:
        raise _DRAFT_BLOCKED
    if require_editor and article.status not in {
        ArticleStatus.SUBMITTED,
        ArticleStatus.UNDER_REVIEW,
    }:
        raise _INVALID_STATUS

    reviews = list(
        db.scalars(
            select(Review).where(Review.article_version_id == version.id)
        ).all()
    )
    disclosure_by_review = _disclosure_map(reviews, disclosures)
    for review in reviews:
        if review.status == ReviewStatus.SUBMITTED:
            review.reveal_reviewer_identity_to_author = disclosure_by_review.get(
                review.id, False
            )

    # An admin may re-enter the same open round to replace its note/disclosures.
    if (
        article.status == ArticleStatus.REVISION_REQUESTED
        and article.revision_requested_for_version_id == version.id
    ):
        article.revision_request_note = normalized_note
        article.revision_requested_by = actor_id
        article.revision_requested_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(version)
        return version

    document = s3.get_json(version.storage_prefix)
    if not isinstance(document, dict):
        raise HTTPException(status_code=503, detail="تعذّر قراءة الإصدار الرسمي.")
    canonical = butex_worker_client.normalize_document(document)
    title, abstract = article_draft_service.document_metadata(canonical)
    document_hash = compile_service.hash_document(canonical)
    if document_hash != version.document_hash:
        raise HTTPException(status_code=409, detail="تعذّر التحقق من سلامة الإصدار الرسمي.")
    _, raw_asset_ids = butex_worker_client.export_document(canonical)
    asset_ids = compile_service.validate_asset_keys(raw_asset_ids)
    for asset_id in asset_ids:
        try:
            s3.assert_exists(article_draft_service.draft_asset_prefix(article.id), asset_id)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            body, content_type = s3.get_bytes(version.storage_prefix, asset_id)
            s3.put_bytes_key_immutable(
                f"{article_draft_service.draft_asset_prefix(article.id)}/{asset_id}",
                body,
                content_type or "application/octet-stream",
            )

    revision_id = uuid.uuid4()
    storage_key = article_draft_service.revision_storage_key(article.id, revision_id)
    s3.put_json_key_immutable(storage_key, canonical)
    revision = ArticleDraftRevision(
        id=revision_id,
        article_id=article.id,
        revision_number=article.draft_revision_number + 1,
        storage_key=storage_key,
        document_hash=document_hash,
        created_by=actor_id,
        actor_type=DraftActorType.HUMAN,
        reason=DraftRevisionReason.REVISION_REQUEST,
        referenced_asset_ids=asset_ids,
    )
    db.add(revision)
    db.flush()
    article.current_draft_revision_id = revision.id
    article.draft_revision_number = revision.revision_number
    article.title = title
    article.abstract = abstract
    article.revision_request_note = normalized_note
    article.revision_requested_for_version_id = version.id
    article.revision_requested_by = actor_id
    article.revision_requested_at = datetime.now(timezone.utc)
    article.status = ArticleStatus.REVISION_REQUESTED
    article.updated_at = datetime.now(timezone.utc)

    workflow_notification_service.notify_many(
        db,
        user_ids=workflow_notification_service.author_ids(article),
        type=NotificationType.EDITORIAL_DECISION,
        title="مطلوب تعديل البحث",
        body=f"طُلبت تعديلات على «{version.title_snapshot}». {normalized_note}",
        link=f"/maktabi/maqalati/{article.id}",
        actor_id=actor_id,
        event_scope=(
            f"article:{article.id}:version:{version.version_number}:revision-request:"
            f"{article.revision_requested_at.isoformat()}"
        ),
        metadata={
            "article_id": str(article.id),
            "version_number": version.version_number,
            "status": ArticleStatus.REVISION_REQUESTED.value,
        },
    )
    pruned = article_draft_service._prune_revisions(db, article.id)
    db.commit()
    db.refresh(version)
    for key, old_revision_id in pruned:
        try:
            s3.delete_key(key)
            s3.delete_prefix(
                f"{article_draft_service.draft_storage_prefix(article.id)}/previews/{old_revision_id}"
            )
        except Exception:
            logger.warning("Failed to clean pruned revision %s", old_revision_id)

    article_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/maqalati/{article.id}"
    for link in article.author_links:
        try:
            email_service.send_decision_email(
                to=link.user.email,
                article_title=version.title_snapshot,
                decision_text="مطلوب تعديل",
                article_url=article_url,
                next_step=normalized_note,
                idempotency_key=(
                    f"revision-request/{article.id}/{version.version_number}/"
                    f"{article.revision_requested_at.isoformat()}/{link.user_id}"
                ),
            )
        except Exception as exc:
            logger.warning("Revision-request email failed for article %s: %s", article.id, exc)
    return version


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
    status: ArticleStatus,
    reason: str | None = None,
    disclosures: list[object] | None = None,
) -> ArticleVersion:
    if status not in _DECISION_ALLOWED:
        raise _INVALID_STATUS
    assert_is_editor(db, article_id, user_id)
    article = db.get(Article, article_id)
    if article is None:
        raise _NOT_FOUND
    version = article_service.latest_version(db, article_id)
    if version is None or article.status == ArticleStatus.DRAFT:
        raise _DRAFT_BLOCKED
    if status == ArticleStatus.REVISION_REQUESTED:
        return request_revisions(
            db,
            article_id,
            user_id,
            reason or "",
            disclosures,
            require_editor=True,
        )
    if status not in _EDITOR_TRANSITIONS.get(article.status, set()):
        raise _INVALID_STATUS
    if article.status == status:
        return version
    transition_marker = datetime.now(timezone.utc).isoformat()

    article.status = status

    label = _STATUS_AR[status]

    article = db.scalar(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.author_links).selectinload(ArticleAuthor.user))
    )
    if article:
        workflow_notification_service.notify_many(
            db,
            user_ids=workflow_notification_service.author_ids(article),
            type=NotificationType.EDITORIAL_DECISION,
            title="قرار تحريري جديد",
            body=(
                f"أصبحت حالة البحث «{version.title_snapshot}»: {label}."
                + (f" {reason.strip()}" if reason and reason.strip() else "")
            ),
            link=f"/maktabi/maqalati/{article.id}",
            actor_id=user_id,
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
    if article:
        article_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/maqalati/{article.id}"
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
