from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DonationEmailReceipt(Base):
    """Minimal durable state used only to avoid duplicate donor emails."""

    __tablename__ = "donation_email_receipts"

    stripe_checkout_session_id: Mapped[str] = mapped_column(
        String(255), primary_key=True
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
