import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import IssueCategory, IssueStatus


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_created_at", "created_at"),
        Index("ix_issues_user_created_at", "user_id", "created_at"),
        Index("ix_issues_status_created_at", "status", "created_at"),
        Index("ix_issues_category_created_at", "category", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus, native_enum=False), default=IssueStatus.OPEN
    )
    category: Mapped[IssueCategory] = mapped_column(
        Enum(IssueCategory, native_enum=False)
    )
    upvote_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    reporter: Mapped["User"] = relationship(back_populates="issues")
    upvotes: Mapped[list["IssueUpvote"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )
    images: Mapped[list["IssueImage"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )


class IssueUpvote(Base):
    __tablename__ = "issue_upvotes"
    __table_args__ = (
        UniqueConstraint("issue_id", "user_id", name="uq_issue_upvotes_issue_user"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    issue: Mapped["Issue"] = relationship(back_populates="upvotes")
    user: Mapped["User"] = relationship(back_populates="issue_upvotes")


class IssueImage(Base):
    __tablename__ = "issue_images"
    __table_args__ = (
        UniqueConstraint("issue_id", "position", name="uq_issue_images_issue_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    issue_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("issues.id", ondelete="CASCADE"), index=True
    )
    s3_key: Mapped[str] = mapped_column(String(500))
    position: Mapped[int] = mapped_column(Integer)

    issue: Mapped["Issue"] = relationship(back_populates="images")
