import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.article import Article, ArticleAuthor, ArticleEditor, ArticleReviewer


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
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
