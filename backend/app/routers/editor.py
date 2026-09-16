import uuid
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.core import s3
from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.schemas.article import VersionRead
from app.schemas.editor import (
    EditorArticleDetail,
    EditorArticleSummary,
    EditorDecisionPayload,
    EditorReviewReport,
)
from app.models.article import ArticleVersion
from app.services import compile_service, editor_service

router = APIRouter(prefix="/api/v1/editor", tags=["editor"])


def _formal_version(db, article_id: uuid.UUID, version_id: uuid.UUID) -> ArticleVersion:
    version = db.get(ArticleVersion, version_id)
    if version is None or version.article_id != article_id:
        raise HTTPException(status_code=404, detail="الإصدار الرسمي غير موجود.")
    return version


def _asset_response(version: ArticleVersion, filename: str) -> Response:
    name = PurePosixPath(filename).name
    if name != filename or not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="اسم ملف غير صالح.")
    body, content_type = s3.get_bytes(version.storage_prefix, f"assets/{name}")
    return Response(
        content=body,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "private, max-age=3600"},
    )


def _pdf_response(version: ArticleVersion) -> Response:
    body = compile_service.get_compiled_pdf(version.storage_prefix)
    return Response(
        content=body,
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Disposition": 'inline; filename="compiled.pdf"',
        },
    )


@router.get("/articles", response_model=list[EditorArticleSummary])
def list_editor_articles(
    auth: AuthDep, db: DbDep
) -> list[EditorArticleSummary]:
    user = current_user(auth, db)
    rows = editor_service.list_articles_for_editor(db, user.id)
    return [
        EditorArticleSummary(
            id=article.id,
            title=version.title_snapshot,
            status=article.status,
            version_number=version.version_number,
            updated_at=article.updated_at,
            submitted_at=version.submitted_at,
            submitted_reviews_count=reviews_count,
        )
        for article, version, reviews_count in rows
    ]


@router.get("/articles/{article_id}", response_model=EditorArticleDetail)
def get_editor_article(
    article_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> EditorArticleDetail:
    user = current_user(auth, db)
    article = editor_service.get_article_for_editor(db, article_id, user.id)
    versions = sorted(article.versions, key=lambda v: v.version_number, reverse=True)
    current = versions[0]
    reviews: list[EditorReviewReport] = []
    for assignment, review in editor_service.submitted_reviews_for_version(
        article, current.id
    ):
        reviews.append(
            EditorReviewReport(
                id=review.id,
                reviewer_name=assignment.user.full_name if assignment.user else None,
                reviewer_email=assignment.user.email if assignment.user else "",
                comments_to_author=review.comments_to_author,
                comments_to_editor=review.comments_to_editor,
                recommendation=review.recommendation,
                submitted_at=review.submitted_at,
                reveal_reviewer_identity_to_author=review.reveal_reviewer_identity_to_author,
            )
        )
    return EditorArticleDetail(
        id=article.id,
        title=current.title_snapshot,
        abstract=current.abstract_snapshot,
        status=article.status,
        created_at=article.created_at,
        updated_at=article.updated_at,
        latest_version=VersionRead.model_validate(current),
        versions=[VersionRead.model_validate(v) for v in versions],
        reviews=reviews,
    )


@router.get("/articles/{article_id}/versions/{version_id}/document")
def get_editor_document(
    article_id: uuid.UUID, version_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> dict:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    version = _formal_version(db, article_id, version_id)
    document = s3.get_json(version.storage_prefix)
    return {"document": document}


@router.get("/articles/{article_id}/versions/{version_id}/assets/{filename}")
def get_editor_asset(
    article_id: uuid.UUID,
    version_id: uuid.UUID,
    filename: str,
    auth: AuthDep,
    db: DbDep,
) -> Response:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    return _asset_response(_formal_version(db, article_id, version_id), filename)


@router.get("/articles/{article_id}/versions/{version_id}/pdf")
def get_editor_pdf(
    article_id: uuid.UUID, version_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> Response:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    return _pdf_response(_formal_version(db, article_id, version_id))


@router.post("/articles/{article_id}/decision", response_model=VersionRead)
def editor_decision(
    article_id: uuid.UUID,
    payload: EditorDecisionPayload,
    auth: AuthDep,
    db: DbDep,
) -> VersionRead:
    # Editorial decisions are authoritative and must stay human-only.
    user = current_user(auth, db)
    version = editor_service.apply_decision(
        db,
        article_id,
        user.id,
        payload.status,
        reason=payload.reason,
        disclosures=payload.reviewer_identity_disclosures,
    )
    return VersionRead.model_validate(version)
