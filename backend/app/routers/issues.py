import uuid
from typing import Literal

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import Response

from app.core import s3
from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.models.enums import IssueCategory, IssueStatus
from app.models.issue import Issue
from app.schemas.issue import (
    IssueCreate,
    IssueImageRead,
    IssueRead,
    IssueReporterRead,
)
from app.services import issue_service

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])


def _read(issue: Issue, current_user_upvoted: bool) -> IssueRead:
    images = sorted(issue.images, key=lambda image: image.position)
    return IssueRead(
        id=issue.id,
        user_id=issue.user_id,
        title=issue.title,
        description=issue.description,
        status=issue.status,
        category=issue.category,
        upvote_count=issue.upvote_count,
        current_user_upvoted=current_user_upvoted,
        reporter=IssueReporterRead(
            id=issue.reporter.id,
            full_name=issue.reporter.full_name,
        ),
        images=[IssueImageRead.model_validate(image) for image in images],
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.get("", response_model=list[IssueRead])
def list_issues(
    auth: AuthDep,
    db: DbDep,
    status: IssueStatus | None = Query(default=None),
    category: IssueCategory | None = Query(default=None),
    sort: Literal["date", "upvotes"] = Query(default="date"),
    direction: Literal["asc", "desc"] = Query(default="desc"),
) -> list[IssueRead]:
    user = current_user(auth, db)
    rows = issue_service.list_issues(
        db,
        status=status,
        category=category,
        sort=sort,
        direction=direction,
    )
    upvoted = issue_service.upvoted_issue_ids(db, user.id, [row.id for row in rows])
    return [_read(row, row.id in upvoted) for row in rows]


@router.post("", response_model=IssueRead, status_code=201)
def create_issue(payload: IssueCreate, auth: AuthDep, db: DbDep) -> IssueRead:
    user = current_user(auth, db)
    issue = issue_service.create_issue(
        db,
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
    )
    issue = issue_service.get_issue(db, issue.id)
    return _read(issue, current_user_upvoted=False)


@router.get("/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: uuid.UUID, auth: AuthDep, db: DbDep) -> IssueRead:
    user = current_user(auth, db)
    issue = issue_service.get_issue(db, issue_id)
    return _read(issue, issue_service.has_upvoted(db, user.id, issue.id))


@router.post("/{issue_id}/images", response_model=IssueRead, status_code=201)
async def upload_issue_image(
    issue_id: uuid.UUID,
    auth: AuthDep,
    db: DbDep,
    file: UploadFile = File(...),
) -> IssueRead:
    user = current_user(auth, db)
    body = await file.read()
    issue = issue_service.create_issue_image(
        db,
        issue_id=issue_id,
        user_id=user.id,
        body=body,
        content_type=file.content_type or "",
    )
    return _read(issue, issue_service.has_upvoted(db, user.id, issue.id))


@router.get("/{issue_id}/images/{image_id}")
def get_issue_image(
    issue_id: uuid.UUID,
    image_id: uuid.UUID,
    auth: AuthDep,
    db: DbDep,
) -> Response:
    current_user(auth, db)
    image = issue_service.get_issue_image(db, issue_id, image_id)
    body, content_type = s3.get_bytes_key(image.s3_key)
    return Response(
        content=body,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.delete("/{issue_id}/images/{image_id}", response_model=IssueRead)
def delete_issue_image(
    issue_id: uuid.UUID,
    image_id: uuid.UUID,
    auth: AuthDep,
    db: DbDep,
) -> IssueRead:
    user = current_user(auth, db)
    issue = issue_service.delete_issue_image(db, issue_id, image_id, user.id)
    return _read(issue, issue_service.has_upvoted(db, user.id, issue.id))


@router.post("/{issue_id}/upvote", response_model=IssueRead)
def upvote_issue(issue_id: uuid.UUID, auth: AuthDep, db: DbDep) -> IssueRead:
    user = current_user(auth, db)
    issue = issue_service.upvote_issue(db, issue_id, user.id)
    return _read(issue, current_user_upvoted=True)


@router.delete("/{issue_id}/upvote", response_model=IssueRead)
def remove_issue_upvote(
    issue_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> IssueRead:
    user = current_user(auth, db)
    issue = issue_service.remove_upvote(db, issue_id, user.id)
    return _read(issue, issue_service.has_upvoted(db, user.id, issue.id))
