import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"
    __table_args__ = (
        Index("ix_email_deliveries_context", "email_kind", "related_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider_email_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    email_kind: Mapped[str] = mapped_column(String(120), index=True)
    recipient_hash: Mapped[str] = mapped_column(String(64), index=True)
    event_scope: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latest_state: Mapped[str] = mapped_column(String(32), default="accepted", index=True)
    latest_provider_event: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latest_provider_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_code: Mapped[str | None] = mapped_column(String(160), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EmailDeliveryEvent(Base):
    __tablename__ = "email_delivery_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("email_deliveries.id", ondelete="CASCADE"),
        index=True,
    )
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(32))
    provider_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
