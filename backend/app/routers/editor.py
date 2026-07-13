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
from app.services import article_service, compile_service, editor_service

router = APIRouter(prefix="/api/v1/editor", tags=["editor"])


def _asset_response(article_id: uuid.UUID, filename: str, db) -> Response:
    name = PurePosixPath(filename).name
    if name != filename or not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="اسم ملف غير صالح.")
    version = article_service.current_version(db, article_id)
    body, content_type = s3.get_bytes(version.storage_prefix, f"assets/{name}")
    return Response(
        content=body,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "private, max-age=3600"},
    )


def _pdf_response(article_id: uuid.UUID, db) -> Response:
    version = article_service.current_version(db, article_id)
    body = compile_service.get_compiled_pdf(version.storage_prefix)
    return Response(
        content=body,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, max-age=60",
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
            title=article.title,
            status=version.status,
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
            )
        )
    return EditorArticleDetail(
        id=article.id,
        title=article.title,
        abstract=article.abstract,
        created_at=article.created_at,
        updated_at=article.updated_at,
        current_version=VersionRead.model_validate(current),
        versions=[VersionRead.model_validate(v) for v in versions],
        reviews=reviews,
    )


@router.get("/articles/{article_id}/document")
def get_editor_document(
    article_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> dict:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    document = s3.get_json(version.storage_prefix)
    return {"document": document}


@router.get("/articles/{article_id}/assets/{filename}")
def get_editor_asset(
    article_id: uuid.UUID,
    filename: str,
    auth: AuthDep,
    db: DbDep,
) -> Response:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    return _asset_response(article_id, filename, db)


@router.get("/articles/{article_id}/pdf")
def get_editor_pdf(
    article_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> Response:
    user = current_user(auth, db)
    editor_service.assert_is_editor(db, article_id, user.id)
    return _pdf_response(article_id, db)


@router.post("/articles/{article_id}/decision", response_model=VersionRead)
def editor_decision(
    article_id: uuid.UUID,
    payload: EditorDecisionPayload,
    auth: AuthDep,
    db: DbDep,
) -> VersionRead:
    user = current_user(auth, db)
    version = editor_service.apply_decision(
        db,
        article_id,
        user.id,
        payload.status,
        reason=payload.reason,
    )
    return VersionRead.model_validate(version)
