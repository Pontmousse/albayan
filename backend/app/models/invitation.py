import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import InvitationRole, InvitationStatus

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.user import User


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[InvitationRole] = mapped_column(
        Enum(InvitationRole, native_enum=False)
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, native_enum=False),
        default=InvitationStatus.PENDING,
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(back_populates="invitations")
    inviter: Mapped["User"] = relationship(back_populates="sent_invitations")
