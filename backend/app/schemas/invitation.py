from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import InvitationRole, InvitationStatus


class InvitationAcceptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_id: UUID
    role: InvitationRole
    email: str
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime
