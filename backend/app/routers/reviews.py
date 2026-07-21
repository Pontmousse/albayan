import uuid
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.core import s3
from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.schemas.review import (
    AssignmentDetail,
    AssignmentSummary,
    ReviewRead,
    ReviewWrite,
)
from app.services import article_service, compile_service, review_service

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


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
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Disposition": 'inline; filename="compiled.pdf"',
        },
    )



def _latest_version(assignment):
    versions = assignment.article.versions
    return max(versions, key=lambda v: v.version_number)


def _review_for_version(assignment, version):
    matches = [r for r in assignment.reviews if r.article_version_id == version.id]
    if not matches:
        return None
    return max(matches, key=lambda r: r.created_at)


def _summary(assignment) -> AssignmentSummary:
    version = _latest_version(assignment)
    review = _review_for_version(assignment, version)
    return AssignmentSummary(
        id=assignment.id,
        article_id=assignment.article_id,
        article_title=assignment.article.title,
        assignment_status=assignment.status,
        version_status=version.status,
        version_number=version.version_number,
        review=ReviewRead.model_validate(review) if review else None,
        invited_at=assignment.invited_at,
    )


def _detail(assignment) -> AssignmentDetail:
    version = _latest_version(assignment)
    review = _review_for_version(assignment, version)
    return AssignmentDetail(
        id=assignment.id,
        article_id=assignment.article_id,
        article_title=assignment.article.title,
        article_abstract=assignment.article.abstract,
        assignment_status=assignment.status,
        version_status=version.status,
        version_number=version.version_number,
        version_id=version.id,
        compile_status=version.compile_status,
        review=ReviewRead.model_validate(review) if review else None,
        invited_at=assignment.invited_at,
        accepted_at=assignment.accepted_at,
    )


@router.get("/me", response_model=list[AssignmentSummary])
def list_my_assignments(auth: AuthDep, db: DbDep) -> list[AssignmentSummary]:
    user = current_user(auth, db)
    rows = review_service.list_assignments_for_reviewer(db, user.id)
    return [_summary(row) for row in rows]


@router.get("/assignments/{assignment_id}", response_model=AssignmentDetail)
def get_assignment(
    assignment_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> AssignmentDetail:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    return _detail(assignment)


@router.get("/assignments/{assignment_id}/document")
def get_assignment_document(
    assignment_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> dict:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    version = article_service.current_version(db, assignment.article_id)
    document = s3.get_json(version.storage_prefix)
    return {"document": document}


@router.get("/assignments/{assignment_id}/assets/{filename}")
def get_assignment_asset(
    assignment_id: uuid.UUID,
    filename: str,
    auth: AuthDep,
    db: DbDep,
) -> Response:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    return _asset_response(assignment.article_id, filename, db)


@router.get("/assignments/{assignment_id}/pdf")
def get_assignment_pdf(
    assignment_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> Response:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    return _pdf_response(assignment.article_id, db)


@router.put("/assignments/{assignment_id}/review", response_model=ReviewRead)
def save_review_draft(
    assignment_id: uuid.UUID,
    payload: ReviewWrite,
    auth: AuthDep,
    db: DbDep,
) -> ReviewRead:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    review = review_service.upsert_draft_review(
        db,
        assignment,
        comments_to_author=payload.comments_to_author,
        comments_to_editor=payload.comments_to_editor,
        recommendation=payload.recommendation,
    )
    return ReviewRead.model_validate(review)


@router.post(
    "/assignments/{assignment_id}/review/submit", response_model=ReviewRead
)
def submit_review(
    assignment_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> ReviewRead:
    user = current_user(auth, db)
    assignment = review_service.get_assignment_for_user(db, assignment_id, user.id)
    review = review_service.submit_review(db, assignment)
    return ReviewRead.model_validate(review)
