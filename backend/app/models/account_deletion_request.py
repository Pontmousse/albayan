import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AccountDeletionRequestStatus

if TYPE_CHECKING:
    from app.models.user import User


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    email_snapshot: Mapped[str] = mapped_column(String(320), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AccountDeletionRequestStatus] = mapped_column(
        String(32),
        default=AccountDeletionRequestStatus.PENDING,
        server_default=AccountDeletionRequestStatus.PENDING.value,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="account_deletion_requests",
    )
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])
