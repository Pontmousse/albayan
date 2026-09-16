import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, ForeignKeyConstraint, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import InvitationRole, InvitationStatus

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.user import User


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(
            "(role = 'REVIEWER' AND article_version_id IS NOT NULL) OR "
            "(role = 'EDITOR' AND article_version_id IS NULL)",
            name="ck_invitations_reviewer_version",
        ),
        ForeignKeyConstraint(
            ["article_version_id", "article_id"],
            ["article_versions.id", "article_versions.article_id"],
            name="fk_invitations_version_article",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    article_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
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
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(
        back_populates="invitations", foreign_keys=[article_id]
    )
    inviter: Mapped["User"] = relationship(back_populates="sent_invitations")
