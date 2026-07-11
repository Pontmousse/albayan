from fastapi import APIRouter

from app.core.clerk import AuthDep, DbDep
from app.core.deps import current_user
from app.schemas.invitation import InvitationAcceptResponse
from app.services import invitation_service

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


@router.post("/{token}/accept", response_model=InvitationAcceptResponse)
def accept_invitation(
    token: str, auth: AuthDep, db: DbDep
) -> InvitationAcceptResponse:
    user = current_user(auth, db)
    invitation = invitation_service.accept_invitation(db, token=token, user=user)
    return InvitationAcceptResponse.model_validate(invitation)
