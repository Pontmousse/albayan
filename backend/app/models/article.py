import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    CompileStatus,
    ReviewRecommendation,
    ReviewStatus,
    ReviewerAssignmentStatus,
    SourceType,
    VersionStatus,
)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    abstract: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    submitter: Mapped["User"] = relationship(back_populates="submitted_articles")
    versions: Mapped[list["ArticleVersion"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    author_links: Mapped[list["ArticleAuthor"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    editor_assignments: Mapped[list["ArticleEditor"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    reviewer_assignments: Mapped[list["ArticleReviewer"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )


class ArticleVersion(Base):
    __tablename__ = "article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version_number", name="uq_article_versions_article_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    storage_prefix: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False),
        default=SourceType.WEB_EDITOR,
    )
    status: Mapped[VersionStatus] = mapped_column(
        Enum(VersionStatus, native_enum=False),
        default=VersionStatus.DRAFT,
        index=True,
    )
    compile_status: Mapped[CompileStatus] = mapped_column(
        Enum(CompileStatus, native_enum=False),
        default=CompileStatus.PENDING,
    )
    active_compile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    compiled_document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(back_populates="versions")
    reviews: Mapped[list["Review"]] = relationship(back_populates="article_version")


class ArticleAuthor(Base):
    __tablename__ = "article_authors"

    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    author_order: Mapped[int] = mapped_column(Integer, default=1)
    is_corresponding: Mapped[bool] = mapped_column(Boolean, default=False)

    article: Mapped["Article"] = relationship(back_populates="author_links")
    user: Mapped["User"] = relationship(back_populates="authored_article_links")


class ArticleEditor(Base):
    __tablename__ = "article_editors"
    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_article_editors_article_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    article: Mapped["Article"] = relationship(back_populates="editor_assignments")
    user: Mapped["User"] = relationship(
        back_populates="editor_assignments",
        foreign_keys=[user_id],
    )
    assigner: Mapped["User | None"] = relationship(
        back_populates="assigned_editor_links",
        foreign_keys=[assigned_by],
    )


class ArticleReviewer(Base):
    __tablename__ = "article_reviewers"
    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_article_reviewers_article_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[ReviewerAssignmentStatus] = mapped_column(
        Enum(ReviewerAssignmentStatus, native_enum=False),
        default=ReviewerAssignmentStatus.INVITED,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    article: Mapped["Article"] = relationship(back_populates="reviewer_assignments")
    user: Mapped["User"] = relationship(back_populates="reviewer_assignments")
    reviews: Mapped[list["Review"]] = relationship(back_populates="article_reviewer")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("article_reviewers.id", ondelete="CASCADE"),
        index=True,
    )
    article_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("article_versions.id", ondelete="RESTRICT"),
        index=True,
    )
    comments_to_author: Mapped[str | None] = mapped_column(Text)
    comments_to_editor: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[ReviewRecommendation | None] = mapped_column(
        Enum(ReviewRecommendation, native_enum=False)
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False),
        default=ReviewStatus.DRAFT,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    article_reviewer: Mapped["ArticleReviewer"] = relationship(
        back_populates="reviews"
    )
    article_version: Mapped["ArticleVersion"] = relationship(back_populates="reviews")
