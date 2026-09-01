import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EmailDigestState(Base):
    __tablename__ = "email_digest_states"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_unread_digest_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    user: Mapped["User"] = relationship(back_populates="email_digest_state")
