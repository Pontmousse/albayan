import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DraftRevisionChangeSummary(Base):
    __tablename__ = "draft_revision_change_summaries"
    __table_args__ = (
        CheckConstraint(
            "schema_version >= 1",
            name="ck_draft_revision_change_summary_version_positive",
        ),
    )

    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("article_draft_revisions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    schema_version: Mapped[int] = mapped_column(Integer)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
