import uuid
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import s3
from app.models.article import (
    Article,
    ArticleAuthor,
    ArticleDraftRevision,
    ArticleEditor,
    ArticleVersion,
)
from app.models.enums import (
    ArticleStatus,
    DraftActorType,
    DraftRevisionReason,
    NotificationType,
    SourceType,
)
from app.models.user import User
from app.core.dates import format_date_time
from app.services import (
    article_draft_service,
    butex_worker_client,
    compile_service,
    email_service,
    workflow_notification_service,
)

_FROZEN = HTTPException(status_code=409, detail="المخطوطة مجمّدة — لا يمكن تعديلها بعد التقديم.")
_ALREADY_SUBMITTED = HTTPException(status_code=409, detail="المقال مُقدَّم بالفعل.")
_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_NOT_DRAFT = HTTPException(
    status_code=409, detail="لا يمكن حذف مقال مُقدَّم."
)

logger = logging.getLogger(__name__)


def assert_is_author(db: Session, article_id: uuid.UUID, user_id: uuid.UUID) -> Article:
    """يعيد المقال إذا كان المستخدم مؤلفاً عليه، وإلا 404 (لا نكشف الوجود)."""
    article = db.get(Article, article_id)
    link = db.scalar(
        select(ArticleAuthor).where(
            ArticleAuthor.article_id == article_id,
            ArticleAuthor.user_id == user_id,
        )
    )
    if not article or not link:
        raise _NOT_FOUND
    return article


def latest_version(db: Session, article_id: uuid.UUID) -> ArticleVersion | None:
    version = db.scalar(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article_id)
        .order_by(ArticleVersion.version_number.desc())
        .limit(1)
    )
    return version


def list_articles_for_author(
    db: Session, user_id: uuid.UUID
) -> list[tuple[Article, ArticleVersion | None]]:
    """مقالات المستخدم كمؤلف، كل مقال مع إصداره الحالي."""
    articles = (
        db.scalars(
            select(Article)
            .join(ArticleAuthor, ArticleAuthor.article_id == Article.id)
            .where(ArticleAuthor.user_id == user_id)
            .options(selectinload(Article.versions))
            .order_by(Article.updated_at.desc())
        )
        .unique()
        .all()
    )
    result = []
    for article in articles:
        latest = (
            max(article.versions, key=lambda v: v.version_number)
            if article.versions
            else None
        )
        result.append((article, latest))
    return result


def create_article(
    db: Session, user_id: uuid.UUID, title: str, abstract: str | None
) -> Article:
    """ينشئ المقال ولقطة المسودة الأولى، من دون أي إصدار رسمي."""
    article_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    document = butex_worker_client.normalize_document(
        article_draft_service.empty_document(title, abstract)
    )
    canonical_title, canonical_abstract = article_draft_service.document_metadata(document)
    # Empty Document2 must still pass the same export validation as later saves.
    _, asset_ids = butex_worker_client.export_document(document)
    if asset_ids:
        raise HTTPException(status_code=422, detail="المسودة الأولية غير صالحة.")
    document_hash = compile_service.hash_document(document)
    storage_key = article_draft_service.revision_storage_key(article_id, revision_id)
    s3.put_json_key_immutable(storage_key, document)

    article = Article(
        id=article_id,
        submitted_by=user_id,
        title=canonical_title,
        abstract=canonical_abstract,
        status=ArticleStatus.DRAFT,
        draft_revision_number=0,
    )
    db.add(article)
    db.flush()
    revision = ArticleDraftRevision(
        id=revision_id,
        article_id=article.id,
        revision_number=1,
        storage_key=storage_key,
        document_hash=document_hash,
        created_by=user_id,
        actor_type=DraftActorType.HUMAN,
        reason=DraftRevisionReason.INITIAL,
        referenced_asset_ids=[],
    )
    db.add(revision)
    db.add(
        ArticleAuthor(
            article_id=article.id,
            user_id=user_id,
            author_order=1,
            is_corresponding=True,
        )
    )
    db.flush()
    article.current_draft_revision_id = revision.id
    article.draft_revision_number = 1
    db.commit()
    db.refresh(article)
    return article


def assert_draft(article: Article) -> None:
    if article.status not in {ArticleStatus.DRAFT, ArticleStatus.REVISION_REQUESTED}:
        raise _FROZEN


def submit_article(db: Session, article: Article) -> ArticleVersion:
    locked_article = db.scalar(
        select(Article)
        .where(Article.id == article.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked_article is None or locked_article.status not in {
        ArticleStatus.DRAFT,
        ArticleStatus.REVISION_REQUESTED,
    }:
        raise _ALREADY_SUBMITTED
    existing_versions = list(
        db.scalars(
            select(ArticleVersion)
            .where(ArticleVersion.article_id == article.id)
            .order_by(ArticleVersion.version_number)
        ).all()
    )
    if locked_article.status == ArticleStatus.DRAFT and existing_versions:
        raise _ALREADY_SUBMITTED
    if locked_article.status == ArticleStatus.REVISION_REQUESTED and not existing_versions:
        raise _ALREADY_SUBMITTED
    revision = article_draft_service.get_current_revision(db, locked_article)
    compile_service.assert_fresh_preview_for_submit(revision)
    document = article_draft_service.read_document(revision)
    title_snapshot, abstract_snapshot = article_draft_service.document_metadata(document)
    _, asset_ids = butex_worker_client.export_document(document)
    asset_ids = compile_service.validate_asset_keys(asset_ids)
    if revision.active_compile_id is None:
        raise HTTPException(status_code=409, detail="أنشئ معاينة حديثة قبل تقديم المقال.")

    version_id = uuid.uuid4()
    version_number = (existing_versions[-1].version_number + 1) if existing_versions else 1
    storage_prefix = f"articles/{article.id}/versions/v{version_number}"
    created_keys: list[str] = []
    try:
        document_key = f"{storage_prefix}/document.json"
        s3.put_json_key_immutable(document_key, document)
        created_keys.append(document_key)
        for asset_id in asset_ids:
            body, content_type = s3.get_bytes(
                article_draft_service.draft_asset_prefix(article.id), asset_id
            )
            destination = f"{storage_prefix}/{asset_id}"
            s3.put_bytes_key_immutable(
                destination, body, content_type or "application/octet-stream"
            )
            created_keys.append(destination)
        preview = article_draft_service.preview_prefix(
            article.id, revision.id, revision.active_compile_id
        )
        pdf, _ = s3.get_bytes(preview, s3.COMPILED_PDF)
        pdf_key = f"{storage_prefix}/{s3.COMPILED_PDF}"
        s3.put_bytes_key_immutable(pdf_key, pdf, "application/pdf")
        created_keys.append(pdf_key)
    except Exception:
        for key in created_keys:
            try:
                s3.delete_key(key)
            except Exception:
                logger.warning("Failed to clean incomplete formal object %s", key)
        raise

    version = ArticleVersion(
        id=version_id,
        article_id=article.id,
        version_number=version_number,
        storage_prefix=storage_prefix,
        source_type=SourceType.WEB_EDITOR,
        source_draft_revision_id=revision.id,
        document_hash=revision.document_hash,
        title_snapshot=title_snapshot,
        abstract_snapshot=abstract_snapshot,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(version)
    locked_article.status = ArticleStatus.SUBMITTED
    author_ids = set(
        db.scalars(
            select(ArticleAuthor.user_id).where(ArticleAuthor.article_id == article.id)
        ).all()
    )
    editor_ids = set(
        db.scalars(
            select(ArticleEditor.user_id).where(ArticleEditor.article_id == article.id)
        ).all()
    )
    admin_ids = workflow_notification_service.admin_ids(db)
    staff_ids = editor_ids | admin_ids
    metadata = {
        "article_id": str(article.id),
        "version_number": version.version_number,
    }
    workflow_notification_service.notify_many(
        db,
        user_ids=author_ids - staff_ids,
        type=NotificationType.ARTICLE_SUBMITTED,
        title="تم استلام إعادة تقديم بحثك" if version_number > 1 else "تم استلام بحثك",
        body=(
            f"استلمت المجلة الإصدار {version_number} من «{title_snapshot}»."
            if version_number > 1
            else f"استلمت المجلة البحث «{title_snapshot}» وبدأت متابعته تحريرياً."
        ),
        link=f"/maktabi/maqalati/{article.id}",
        event_scope=f"article:{article.id}:version:{version.version_number}:submitted:author",
        metadata=metadata,
    )
    workflow_notification_service.notify_many(
        db,
        user_ids=editor_ids,
        type=NotificationType.ARTICLE_SUBMITTED,
        title="إعادة تقديم بانتظار المتابعة" if version_number > 1 else "بحث جديد بانتظار المتابعة",
        body=f"قُدّم الإصدار {version_number} من «{title_snapshot}» للمتابعة التحريرية.",
        link=f"/maktabi/tahriri/{article.id}",
        event_scope=f"article:{article.id}:version:{version.version_number}:submitted:editor",
        metadata=metadata,
    )
    workflow_notification_service.notify_many(
        db,
        user_ids=admin_ids - editor_ids,
        type=NotificationType.ARTICLE_SUBMITTED,
        title="إعادة تقديم بانتظار المتابعة" if version_number > 1 else "بحث جديد بانتظار المتابعة",
        body=f"قُدّم الإصدار {version_number} من «{title_snapshot}» للمراجعة التحريرية.",
        link=f"/admin/maqalat/{article.id}",
        event_scope=f"article:{article.id}:version:{version.version_number}:submitted:admin",
        metadata=metadata,
    )
    db.commit()
    db.refresh(version)
    db.refresh(locked_article)
    article_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/maqalati/{article.id}"
    admin_url = f"{email_service.settings.frontend_base_url.rstrip('/')}/admin/maqalat/{article.id}"
    submitted_text = format_date_time(version.submitted_at) if version.submitted_at else ""
    submitter = db.get(User, article.submitted_by)
    if submitter:
        try:
            email_service.send_submission_received_email(
                to=submitter.email,
                article_title=title_snapshot,
                article_url=article_url,
                submitted_text=submitted_text,
                version_number=version.version_number,
            )
        except Exception as exc:
            logger.warning("Submission receipt email failed for article %s: %s", article.id, exc)

    staff_users = list(
        db.scalars(select(User).where(User.id.in_(staff_ids))).all()
    ) if staff_ids else []
    author_name = submitter.full_name if submitter and submitter.full_name else "مؤلف"
    sent_emails: set[str] = set()
    for recipient in staff_users:
        normalized_email = recipient.email.strip().lower()
        if normalized_email in sent_emails:
            continue
        sent_emails.add(normalized_email)
        try:
            email_service.send_new_submission_alert_email(
                to=recipient.email,
                article_title=title_snapshot,
                author_name=author_name,
                article_url=(
                    f"{email_service.settings.frontend_base_url.rstrip('/')}/maktabi/tahriri/{article.id}"
                    if recipient.id in editor_ids
                    else admin_url
                ),
                version_number=version.version_number,
                idempotency_key=(
                    f"new-submission/{article.id}/{version.version_number}/{recipient.id}"
                ),
            )
        except Exception as exc:
            logger.warning(
                "New submission email failed for article %s recipient %s: %s",
                article.id,
                recipient.id,
                exc,
            )
    return version


def delete_draft_article(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """يحذف مسودة المؤلف مع ملفات التخزين — يرفض غير المسودات."""
    article = assert_is_author(db, article_id, user_id)
    if article.status != ArticleStatus.DRAFT:
        raise _NOT_DRAFT

    # أولاً التخزين — إن فشل لا نحذف صف DB
    s3.delete_prefix(f"articles/{article_id}/")

    db.delete(article)
    db.commit()
