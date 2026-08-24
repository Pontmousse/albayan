from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import Article, ArticleAuthor, ArticleVersion
from app.models.enums import VersionStatus
from app.schemas.public import PublicArticleAuthor, PublicArticleSummary


def _latest_version(article: Article) -> ArticleVersion | None:
    if not article.versions:
        return None
    return max(article.versions, key=lambda version: version.version_number)


def list_published_articles(db: Session) -> list[tuple[Article, ArticleVersion]]:
    """المقالات التي إصدارها الحالي منشور — مرتبة من الأحدث."""
    articles = (
        db.scalars(
            select(Article)
            .options(
                selectinload(Article.versions),
                selectinload(Article.author_links).selectinload(ArticleAuthor.user),
            )
            .order_by(Article.updated_at.desc())
        )
        .unique()
        .all()
    )
    published: list[tuple[Article, ArticleVersion]] = []
    for article in articles:
        version = _latest_version(article)
        if version is None or version.status != VersionStatus.PUBLISHED:
            continue
        published.append((article, version))
    published.sort(
        key=lambda pair: pair[1].submitted_at or pair[0].updated_at,
        reverse=True,
    )
    return published


def public_journal_summary(db: Session) -> tuple[int, list[PublicArticleSummary]]:
    rows = list_published_articles(db)
    summaries: list[PublicArticleSummary] = []
    for article, version in rows:
        authors = sorted(article.author_links, key=lambda link: link.author_order)
        summaries.append(
            PublicArticleSummary(
                id=article.id,
                title=article.title,
                abstract=article.abstract,
                published_at=version.submitted_at or article.updated_at,
                authors=[
                    PublicArticleAuthor(
                        full_name=link.user.full_name,
                        author_order=link.author_order,
                    )
                    for link in authors
                ],
            )
        )
    return len(summaries), summaries
