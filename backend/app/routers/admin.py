import uuid
from pathlib import PurePosixPath
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core import s3
from app.core.clerk import AdminDep, DbDep
from app.core.deps import current_user
from app.models.article import ArticleVersion
from app.models.enums import ArticleStatus, InvitationRole, IssueCategory, IssueStatus
from app.models.issue import Issue
from app.schemas.admin import (
    AccountDeletionRequestAdminRead,
    AccountDeletionRequestStatusPayload,
    AdminArticleDetail,
    AdminArticleSummary,
    AdminAuthorRead,
    AdminEditorRead,
    AdminIssueRead,
    AdminIssueReporterRead,
    AdminIssueStatusPayload,
    AdminReviewerRead,
    AdminStatusPayload,
    AdminUserBrief,
    AdminUserListItem,
    AppInvitationCreatePayload,
    AppInvitationCreateResponse,
    AppInvitationRead,
    AssignByUserOrEmail,
    InvitationCreateResponse,
    InvitationRead,
    InviteCreatePayload,
    OverrideDecisionPayload,
)
from app.schemas.article import VersionRead
from app.schemas.editor import EditorReviewReport
from app.schemas.issue import IssueImageRead
from app.services import (
    account_deletion_service,
    admin_article_service,
    admin_issue_service,
    admin_user_service,
    app_invitation_service,
    invitation_service,
    editor_service,
    compile_service,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _formal_version(db, article_id: uuid.UUID, version_id: uuid.UUID) -> ArticleVersion:
    version = db.get(ArticleVersion, version_id)
    if version is None or version.article_id != article_id:
        raise HTTPException(status_code=404, detail="الإصدار الرسمي غير موجود.")
    return version


def _admin_user(auth: AdminDep, db: DbDep):
    user = current_user(auth, db)
    if not user.is_admin:
        user.is_admin = True
        db.commit()
        db.refresh(user)
    return user


def _author_reads(article) -> list[AdminAuthorRead]:
    return [
        AdminAuthorRead(
            user=AdminUserBrief.model_validate(link.user),
            author_order=link.author_order,
            is_corresponding=link.is_corresponding,
        )
        for link in sorted(article.author_links, key=lambda a: a.author_order)
    ]


def _reviewer_reads(article) -> list[AdminReviewerRead]:
    version_numbers = {version.id: version.version_number for version in article.versions}
    return [
        AdminReviewerRead(
            id=a.id,
            user=AdminUserBrief.model_validate(a.user),
            article_version_id=a.article_version_id,
            version_number=version_numbers[a.article_version_id],
            status=a.status,
            invited_at=a.invited_at,
            review_due_at=a.review_due_at,
            accepted_at=a.accepted_at,
            declined_at=a.declined_at,
        )
        for a in article.reviewer_assignments
    ]


def _editor_reads(article) -> list[AdminEditorRead]:
    return [
        AdminEditorRead(
            user=AdminUserBrief.model_validate(a.user),
            assigned_at=a.assigned_at,
            assigned_by=a.assigned_by,
        )
        for a in article.editor_assignments
    ]


def _summary(article, version) -> AdminArticleSummary:
    return AdminArticleSummary(
        id=article.id,
        title=version.title_snapshot if version else article.title,
        status=article.status,
        latest_version_number=version.version_number if version else None,
        updated_at=article.updated_at,
        submitted_at=version.submitted_at if version else None,
        authors=_author_reads(article),
        reviewers=_reviewer_reads(article),
        editors=_editor_reads(article),
    )


def _detail(article) -> AdminArticleDetail:
    versions = sorted(article.versions, key=lambda v: v.version_number, reverse=True)
    latest = versions[0] if versions else None
    reviews = []
    if latest:
        for assignment, review in editor_service.submitted_reviews_for_version(
            article, latest.id
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
    return AdminArticleDetail(
        id=article.id,
        title=latest.title_snapshot if latest else article.title,
        abstract=latest.abstract_snapshot if latest else article.abstract,
        status=article.status,
        created_at=article.created_at,
        updated_at=article.updated_at,
        latest_version=VersionRead.model_validate(latest) if latest else None,
        versions=[VersionRead.model_validate(v) for v in versions],
        authors=_author_reads(article),
        reviewers=_reviewer_reads(article),
        editors=_editor_reads(article),
        reviews=reviews,
        revision_request_note=article.revision_request_note,
    )


def _admin_issue_read(issue: Issue) -> AdminIssueRead:
    images = sorted(issue.images, key=lambda image: image.position)
    return AdminIssueRead(
        id=issue.id,
        user_id=issue.user_id,
        title=issue.title,
        description=issue.description,
        status=issue.status,
        category=issue.category,
        upvote_count=issue.upvote_count,
        reporter=AdminIssueReporterRead(
            id=issue.reporter.id,
            email=issue.reporter.email,
            full_name=issue.reporter.full_name,
        ),
        images=[IssueImageRead.model_validate(image) for image in images],
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.get("/articles", response_model=list[AdminArticleSummary])
def list_admin_articles(
    auth: AdminDep,
    db: DbDep,
    status: ArticleStatus | None = Query(default=None),
) -> list[AdminArticleSummary]:
    _admin_user(auth, db)
    rows = admin_article_service.list_articles(db, status=status)
    return [_summary(article, version) for article, version in rows]


@router.get("/issues", response_model=list[AdminIssueRead])
def list_admin_issues(
    auth: AdminDep,
    db: DbDep,
    status: IssueStatus | None = Query(default=None),
    category: IssueCategory | None = Query(default=None),
    sort: Literal["date", "upvotes"] = Query(default="date"),
    direction: Literal["asc", "desc"] = Query(default="desc"),
) -> list[AdminIssueRead]:
    _admin_user(auth, db)
    rows = admin_issue_service.list_issues(
        db,
        status=status,
        category=category,
        sort=sort,
        direction=direction,
    )
    return [_admin_issue_read(issue) for issue in rows]


@router.patch("/issues/{issue_id}/status", response_model=AdminIssueRead)
def update_admin_issue_status(
    issue_id: uuid.UUID,
    payload: AdminIssueStatusPayload,
    auth: AdminDep,
    db: DbDep,
) -> AdminIssueRead:
    admin = _admin_user(auth, db)
    issue = admin_issue_service.update_issue_status(
        db,
        issue_id=issue_id,
        admin_id=admin.id,
        status=payload.status,
    )
    return _admin_issue_read(issue)


@router.get("/articles/{article_id}", response_model=AdminArticleDetail)
def get_admin_article(
    article_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> AdminArticleDetail:
    _admin_user(auth, db)
    article = admin_article_service.get_article_or_404(db, article_id)
    return _detail(article)


@router.get("/articles/{article_id}/versions/{version_id}/document")
def get_admin_version_document(
    article_id: uuid.UUID, version_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> dict:
    _admin_user(auth, db)
    version = _formal_version(db, article_id, version_id)
    return {"document": s3.get_json(version.storage_prefix)}


@router.get("/articles/{article_id}/versions/{version_id}/pdf")
def get_admin_version_pdf(
    article_id: uuid.UUID, version_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> Response:
    _admin_user(auth, db)
    version = _formal_version(db, article_id, version_id)
    return Response(
        content=compile_service.get_compiled_pdf(version.storage_prefix),
        media_type="application/pdf",
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/articles/{article_id}/versions/{version_id}/assets/{filename}")
def get_admin_version_asset(
    article_id: uuid.UUID,
    version_id: uuid.UUID,
    filename: str,
    auth: AdminDep,
    db: DbDep,
) -> Response:
    _admin_user(auth, db)
    name = PurePosixPath(filename).name
    if name != filename or not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="اسم ملف غير صالح.")
    version = _formal_version(db, article_id, version_id)
    body, content_type = s3.get_bytes(version.storage_prefix, f"assets/{name}")
    return Response(content=body, media_type=content_type or "application/octet-stream")


@router.post("/articles/{article_id}/assign-reviewer", status_code=201)
def assign_reviewer(
    article_id: uuid.UUID,
    payload: AssignByUserOrEmail,
    auth: AdminDep,
    db: DbDep,
) -> dict:
    admin = _admin_user(auth, db)
    if payload.user_id:
        assignment = admin_article_service.assign_reviewer(
            db,
            article_id,
            user_id=payload.user_id,
            assigner_id=admin.id,
            review_due_at=payload.review_due_at,
        )
        return {"ok": True, "assignment_id": str(assignment.id)}

    invitation, warning = invitation_service.create_invitation(
        db,
        article_id=article_id,
        role=InvitationRole.REVIEWER,
        email=str(payload.email),
        invited_by=admin.id,
        review_due_at=payload.review_due_at,
    )
    return {
        "ok": True,
        "invitation_id": str(invitation.id),
        "warning": warning,
    }


@router.post("/articles/{article_id}/assign-editor", status_code=201)
def assign_editor(
    article_id: uuid.UUID,
    payload: AssignByUserOrEmail,
    auth: AdminDep,
    db: DbDep,
) -> dict:
    admin = _admin_user(auth, db)
    if payload.user_id:
        assignment = admin_article_service.assign_editor(
            db, article_id, user_id=payload.user_id, assigner_id=admin.id
        )
        return {"ok": True, "assignment_id": str(assignment.id)}

    invitation, warning = invitation_service.create_invitation(
        db,
        article_id=article_id,
        role=InvitationRole.EDITOR,
        email=str(payload.email),
        invited_by=admin.id,
        review_due_at=payload.review_due_at,
    )
    return {
        "ok": True,
        "invitation_id": str(invitation.id),
        "warning": warning,
    }


@router.delete(
    "/articles/{article_id}/reviewer-assignments/{assignment_id}", status_code=204
)
def unassign_reviewer(
    article_id: uuid.UUID, assignment_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> None:
    admin = _admin_user(auth, db)
    admin_article_service.unassign_reviewer(
        db, article_id, assignment_id, actor_id=admin.id
    )


@router.delete("/articles/{article_id}/editors/{user_id}", status_code=204)
def unassign_editor(
    article_id: uuid.UUID, user_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> None:
    admin = _admin_user(auth, db)
    admin_article_service.unassign_editor(
        db, article_id, user_id, actor_id=admin.id
    )


@router.post(
    "/articles/{article_id}/override-decision", response_model=VersionRead
)
def override_decision(
    article_id: uuid.UUID,
    payload: OverrideDecisionPayload,
    auth: AdminDep,
    db: DbDep,
) -> VersionRead:
    admin = _admin_user(auth, db)
    version = admin_article_service.override_decision(
        db,
        article_id,
        payload.status,
        actor_id=admin.id,
        reason=payload.reason,
        disclosures=payload.reviewer_identity_disclosures,
    )
    return VersionRead.model_validate(version)


@router.get("/users", response_model=list[AdminUserListItem])
def list_admin_users(auth: AdminDep, db: DbDep) -> list[AdminUserListItem]:
    _admin_user(auth, db)
    rows = admin_user_service.list_users_with_roles(db)
    return [AdminUserListItem.model_validate(row) for row in rows]


@router.get("/invitations", response_model=list[AppInvitationRead])
def list_app_invitations(auth: AdminDep, db: DbDep) -> list[AppInvitationRead]:
    _admin_user(auth, db)
    rows = app_invitation_service.list_app_invitations()
    return [AppInvitationRead(**row.__dict__) for row in rows]


@router.post(
    "/invitations",
    response_model=AppInvitationCreateResponse,
    status_code=201,
)
def create_app_invitation(
    payload: AppInvitationCreatePayload, auth: AdminDep, db: DbDep
) -> AppInvitationCreateResponse:
    _admin_user(auth, db)
    invitation = app_invitation_service.create_app_invitation(
        email=payload.email,
        full_name=payload.full_name,
        gender=payload.gender,
        admin=auth,
    )
    return AppInvitationCreateResponse(
        invitation=AppInvitationRead(**invitation.__dict__)
    )


@router.patch("/users/{user_id}/admin-status")
def patch_admin_status(
    user_id: uuid.UUID,
    payload: AdminStatusPayload,
    auth: AdminDep,
    db: DbDep,
) -> dict:
    admin = _admin_user(auth, db)
    user = admin_user_service.set_admin_status(
        db, user_id, payload.is_admin, actor_id=admin.id
    )
    return {
        "ok": True,
        "user_id": str(user.id),
        "is_admin": payload.is_admin,
    }


@router.get(
    "/account-deletion-requests",
    response_model=list[AccountDeletionRequestAdminRead],
)
def list_account_deletion_requests(
    auth: AdminDep, db: DbDep
) -> list[AccountDeletionRequestAdminRead]:
    _admin_user(auth, db)
    rows = account_deletion_service.list_deletion_requests(db)
    return [AccountDeletionRequestAdminRead.model_validate(row) for row in rows]


@router.patch(
    "/account-deletion-requests/{request_id}",
    response_model=AccountDeletionRequestAdminRead,
)
def patch_account_deletion_request(
    request_id: uuid.UUID,
    payload: AccountDeletionRequestStatusPayload,
    auth: AdminDep,
    db: DbDep,
) -> AccountDeletionRequestAdminRead:
    admin_user = _admin_user(auth, db)
    request = account_deletion_service.update_deletion_request_status(
        db,
        request_id=request_id,
        admin=admin_user,
        status=payload.status,
        resolution_note=payload.resolution_note,
    )
    return AccountDeletionRequestAdminRead.model_validate(request)


@router.post(
    "/articles/{article_id}/invite",
    response_model=InvitationCreateResponse,
    status_code=201,
)
def invite_to_article(
    article_id: uuid.UUID,
    payload: InviteCreatePayload,
    auth: AdminDep,
    db: DbDep,
) -> InvitationCreateResponse:
    admin = _admin_user(auth, db)
    invitation, warning = invitation_service.create_invitation(
        db,
        article_id=article_id,
        role=payload.role,
        email=str(payload.email),
        invited_by=admin.id,
        review_due_at=payload.review_due_at,
    )
    return InvitationCreateResponse(
        invitation=InvitationRead.model_validate(invitation),
        warning=warning,
    )


@router.get(
    "/articles/{article_id}/invitations",
    response_model=list[InvitationRead],
)
def list_article_invitations(
    article_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> list[InvitationRead]:
    _admin_user(auth, db)
    rows = invitation_service.list_invitations(db, article_id)
    return [InvitationRead.model_validate(row) for row in rows]


@router.post("/invitations/{invitation_id}/resend")
def resend_invitation(
    invitation_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> dict:
    _admin_user(auth, db)
    invitation = invitation_service.resend_invitation(db, invitation_id)
    return {"ok": True, "invitation_id": str(invitation.id)}


@router.delete("/invitations/{invitation_id}", status_code=204)
def cancel_invitation(
    invitation_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> None:
    _admin_user(auth, db)
    invitation_service.cancel_invitation(db, invitation_id)


@router.post("/invitations/{invitation_id}/revoke", status_code=204)
def revoke_app_invitation(invitation_id: str, auth: AdminDep, db: DbDep) -> None:
    _admin_user(auth, db)
    app_invitation_service.revoke_app_invitation(invitation_id)


@router.post("/app-invitations/{invitation_id}/resend", response_model=AppInvitationRead)
def resend_app_invitation(
    invitation_id: str, auth: AdminDep, db: DbDep
) -> AppInvitationRead:
    _admin_user(auth, db)
    invitation = app_invitation_service.resend_app_invitation(invitation_id)
    return AppInvitationRead(**invitation.__dict__)
