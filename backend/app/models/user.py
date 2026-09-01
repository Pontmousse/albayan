import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserGender

if TYPE_CHECKING:
    from app.models.agent_token import AgentToken
    from app.models.article import Article, ArticleAuthor, ArticleEditor, ArticleReviewer
    from app.models.issue import Issue, IssueUpvote
    from app.models.invitation import Invitation
    from app.models.notification import Notification
    from app.models.account_deletion_request import AccountDeletionRequest
    from app.models.email_digest_state import EmailDigestState


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "gender IS NULL OR gender IN ('male', 'female')",
            name="ck_users_gender",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    gender: Mapped[UserGender | None] = mapped_column(
        Enum(
            UserGender,
            native_enum=False,
            length=6,
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=True,
    )
    affiliation: Mapped[str | None] = mapped_column(String(300))
    bio: Mapped[str | None] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    submitted_articles: Mapped[list["Article"]] = relationship(
        back_populates="submitter"
    )
    authored_article_links: Mapped[list["ArticleAuthor"]] = relationship(
        back_populates="user"
    )
    editor_assignments: Mapped[list["ArticleEditor"]] = relationship(
        back_populates="user",
        foreign_keys="ArticleEditor.user_id",
    )
    assigned_editor_links: Mapped[list["ArticleEditor"]] = relationship(
        back_populates="assigner",
        foreign_keys="ArticleEditor.assigned_by",
    )
    reviewer_assignments: Mapped[list["ArticleReviewer"]] = relationship(
        back_populates="user"
    )
    sent_invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="inviter"
    )
    agent_tokens: Mapped[list["AgentToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="recipient",
        cascade="all, delete-orphan",
        foreign_keys="Notification.user_id",
    )
    triggered_notifications: Mapped[list["Notification"]] = relationship(
        back_populates="actor",
        foreign_keys="Notification.actor_id",
    )
    issues: Mapped[list["Issue"]] = relationship(back_populates="reporter")
    issue_upvotes: Mapped[list["IssueUpvote"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    account_deletion_requests: Mapped[list["AccountDeletionRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AccountDeletionRequest.user_id",
    )
    email_digest_state: Mapped["EmailDigestState | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
    )
