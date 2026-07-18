import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core import s3
from app.models.article import Article, ArticleAuthor, ArticleVersion, Review
from app.models.enums import SourceType, VersionStatus

_FROZEN = HTTPException(status_code=409, detail="المخطوطة مجمّدة — لا يمكن تعديلها بعد التقديم.")
_ALREADY_SUBMITTED = HTTPException(status_code=409, detail="المقال مُقدَّم بالفعل.")
_NOT_FOUND = HTTPException(status_code=404, detail="المقال غير موجود.")
_NOT_DRAFT = HTTPException(
    status_code=409, detail="لا يمكن حذف مقال مُقدَّم."
)


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


def current_version(db: Session, article_id: uuid.UUID) -> ArticleVersion:
    version = db.scalar(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article_id)
        .order_by(ArticleVersion.version_number.desc())
        .limit(1)
    )
    if not version:
        raise _NOT_FOUND
    return version


def list_articles_for_author(db: Session, user_id: uuid.UUID) -> list[tuple[Article, ArticleVersion]]:
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
        if not article.versions:
            continue
        latest = max(article.versions, key=lambda v: v.version_number)
        result.append((article, latest))
    return result


def create_article(
    db: Session, user_id: uuid.UUID, title: str, abstract: str | None
) -> Article:
    """ينشئ article + إصدار v1 (draft) + ربط المؤلف في transaction واحدة."""
    article = Article(submitted_by=user_id, title=title, abstract=abstract)
    db.add(article)
    db.flush()  # نحتاج article.id لبناء storage_prefix

    version = ArticleVersion(
        article_id=article.id,
        version_number=1,
        storage_prefix=f"articles/{article.id}/versions/v1/",
        source_type=SourceType.WEB_EDITOR,
        status=VersionStatus.DRAFT,
    )
    db.add(version)
    db.add(
        ArticleAuthor(
            article_id=article.id,
            user_id=user_id,
            author_order=1,
            is_corresponding=True,
        )
    )
    db.commit()
    db.refresh(article)
    return article


def assert_draft(version: ArticleVersion) -> None:
    if version.status != VersionStatus.DRAFT:
        raise _FROZEN


def submit_article(db: Session, article: Article) -> ArticleVersion:
    version = current_version(db, article.id)
    if version.status != VersionStatus.DRAFT:
        raise _ALREADY_SUBMITTED
    version.status = VersionStatus.SUBMITTED
    version.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(version)
    return version


def delete_draft_article(
    db: Session, article_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """يحذف مسودة المؤلف مع ملفات التخزين — يرفض غير المسودات."""
    article = assert_is_author(db, article_id, user_id)
    version = current_version(db, article_id)
    if version.status != VersionStatus.DRAFT:
        raise _NOT_DRAFT

    version_ids = [
        row.id
        for row in db.scalars(
            select(ArticleVersion).where(ArticleVersion.article_id == article_id)
        ).all()
    ]
    if version_ids:
        db.execute(delete(Review).where(Review.article_version_id.in_(version_ids)))
        db.flush()

    # أولاً التخزين — إن فشل لا نحذف صف DB
    s3.delete_prefix(f"articles/{article_id}/")

    db.delete(article)
    db.commit()
