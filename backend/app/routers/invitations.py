from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import OperationalError

from app.core.clerk import AuthDep, DbDep
from app.schemas.invitation import InvitationAcceptResponse
from app.services import invitation_service
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


@router.post("/{token}/accept", response_model=InvitationAcceptResponse)
def accept_invitation(
    token: str, auth: AuthDep, db: DbDep
) -> InvitationAcceptResponse:
    try:
        user = get_or_create_user(db, auth)
    except OperationalError as exc:
        raise HTTPException(
            status_code=503, detail="الخدمة غير متاحة مؤقتاً."
        ) from exc

    invitation = invitation_service.accept_invitation(db, token=token, user=user)
    return InvitationAcceptResponse.model_validate(invitation)
