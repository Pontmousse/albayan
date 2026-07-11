import uuid

from fastapi import APIRouter, Query

from app.core.clerk import AdminDep, DbDep
from app.core.deps import current_user
from app.models.enums import InvitationRole, VersionStatus
from app.schemas.admin import (
    AdminArticleDetail,
    AdminArticleSummary,
    AdminAuthorRead,
    AdminEditorRead,
    AdminReviewerRead,
    AdminStatusPayload,
    AdminUserBrief,
    AdminUserListItem,
    AssignByUserOrEmail,
    InvitationCreateResponse,
    InvitationRead,
    InviteCreatePayload,
    OverrideDecisionPayload,
)
from app.schemas.article import VersionRead
from app.services import admin_article_service, admin_user_service, invitation_service

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _admin_user(auth: AdminDep, db: DbDep):
    return current_user(auth, db)


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
    return [
        AdminReviewerRead(
            user=AdminUserBrief.model_validate(a.user),
            status=a.status,
            invited_at=a.invited_at,
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
        title=article.title,
        status=version.status,
        version_number=version.version_number,
        updated_at=article.updated_at,
        submitted_at=version.submitted_at,
        authors=_author_reads(article),
        reviewers=_reviewer_reads(article),
        editors=_editor_reads(article),
    )


def _detail(article) -> AdminArticleDetail:
    versions = sorted(article.versions, key=lambda v: v.version_number, reverse=True)
    current = versions[0]
    return AdminArticleDetail(
        id=article.id,
        title=article.title,
        abstract=article.abstract,
        created_at=article.created_at,
        updated_at=article.updated_at,
        current_version=VersionRead.model_validate(current),
        versions=[VersionRead.model_validate(v) for v in versions],
        authors=_author_reads(article),
        reviewers=_reviewer_reads(article),
        editors=_editor_reads(article),
    )


@router.get("/articles", response_model=list[AdminArticleSummary])
def list_admin_articles(
    auth: AdminDep,
    db: DbDep,
    status: VersionStatus | None = Query(default=None),
) -> list[AdminArticleSummary]:
    _admin_user(auth, db)
    rows = admin_article_service.list_articles(db, status=status)
    return [_summary(article, version) for article, version in rows]


@router.get("/articles/{article_id}", response_model=AdminArticleDetail)
def get_admin_article(
    article_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> AdminArticleDetail:
    _admin_user(auth, db)
    article = admin_article_service.get_article_or_404(db, article_id)
    return _detail(article)


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
            db, article_id, user_id=payload.user_id, assigner_id=admin.id
        )
        return {"ok": True, "assignment_id": str(assignment.id)}

    invitation, warning = invitation_service.create_invitation(
        db,
        article_id=article_id,
        role=InvitationRole.REVIEWER,
        email=str(payload.email),
        invited_by=admin.id,
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
    )
    return {
        "ok": True,
        "invitation_id": str(invitation.id),
        "warning": warning,
    }


@router.delete(
    "/articles/{article_id}/reviewers/{user_id}", status_code=204
)
def unassign_reviewer(
    article_id: uuid.UUID, user_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> None:
    _admin_user(auth, db)
    admin_article_service.unassign_reviewer(db, article_id, user_id)


@router.delete("/articles/{article_id}/editors/{user_id}", status_code=204)
def unassign_editor(
    article_id: uuid.UUID, user_id: uuid.UUID, auth: AdminDep, db: DbDep
) -> None:
    _admin_user(auth, db)
    admin_article_service.unassign_editor(db, article_id, user_id)


@router.post(
    "/articles/{article_id}/override-decision", response_model=VersionRead
)
def override_decision(
    article_id: uuid.UUID,
    payload: OverrideDecisionPayload,
    auth: AdminDep,
    db: DbDep,
) -> VersionRead:
    _admin_user(auth, db)
    # reason accepted but not persisted (no audit log in this phase)
    _ = payload.reason
    version = admin_article_service.override_decision(
        db, article_id, payload.status
    )
    return VersionRead.model_validate(version)


@router.get("/users", response_model=list[AdminUserListItem])
def list_admin_users(auth: AdminDep, db: DbDep) -> list[AdminUserListItem]:
    _admin_user(auth, db)
    rows = admin_user_service.list_users_with_roles(db)
    return [AdminUserListItem.model_validate(row) for row in rows]


@router.patch("/users/{user_id}/admin-status")
def patch_admin_status(
    user_id: uuid.UUID,
    payload: AdminStatusPayload,
    auth: AdminDep,
    db: DbDep,
) -> dict:
    _admin_user(auth, db)
    user = admin_user_service.set_admin_status(db, user_id, payload.is_admin)
    return {
        "ok": True,
        "user_id": str(user.id),
        "is_admin": payload.is_admin,
    }


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
