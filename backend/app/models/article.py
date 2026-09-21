import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    ArticleStatus,
    CompileStatus,
    DraftActorType,
    DraftRevisionReason,
    ReviewRecommendation,
    ReviewStatus,
    ReviewerAssignmentStatus,
    SourceType,
)


def _enum_values(enum_class):
    return [member.value for member in enum_class]


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "draft_revision_number >= 0",
            name="ck_articles_draft_revision_number_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    abstract: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus, native_enum=False, values_callable=_enum_values),
        default=ArticleStatus.DRAFT,
        index=True,
    )
    current_draft_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("article_draft_revisions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        index=True,
    )
    draft_revision_number: Mapped[int] = mapped_column(Integer, default=0)
    equation_mappings: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    revision_request_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_requested_for_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("article_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    revision_requested_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revision_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    submitter: Mapped["User"] = relationship(
        back_populates="submitted_articles", foreign_keys=[submitted_by]
    )
    versions: Mapped[list["ArticleVersion"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="ArticleVersion.article_id",
    )
    author_links: Mapped[list["ArticleAuthor"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    editor_assignments: Mapped[list["ArticleEditor"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    reviewer_assignments: Mapped[list["ArticleReviewer"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="ArticleReviewer.article_id",
    )
    draft_revisions: Mapped[list["ArticleDraftRevision"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="ArticleDraftRevision.article_id",
    )
    current_draft_revision: Mapped["ArticleDraftRevision | None"] = relationship(
        foreign_keys=[current_draft_revision_id], post_update=True
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="Invitation.article_id",
    )


class ArticleVersion(Base):
    __tablename__ = "article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version_number", name="uq_article_versions_article_version"),
        UniqueConstraint("id", "article_id", name="uq_article_versions_id_article"),
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
        Enum(SourceType, native_enum=False, values_callable=_enum_values),
        default=SourceType.WEB_EDITOR,
    )
    source_draft_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    document_hash: Mapped[str] = mapped_column(String(64))
    title_snapshot: Mapped[str] = mapped_column(String(500))
    abstract_snapshot: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(
        back_populates="versions", foreign_keys=[article_id]
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="article_version", passive_deletes=True
    )


class ArticleDraftRevision(Base):
    __tablename__ = "article_draft_revisions"
    __table_args__ = (
        UniqueConstraint(
            "article_id", "revision_number", name="uq_draft_revision_article_number"
        ),
        UniqueConstraint("storage_key", name="uq_draft_revision_storage_key"),
        CheckConstraint("revision_number >= 1", name="ck_draft_revision_number_positive"),
        CheckConstraint(
            "restored_from_revision_number IS NULL OR restored_from_revision_number >= 1",
            name="ck_draft_revision_restored_number_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(700))
    document_hash: Mapped[str] = mapped_column(String(64))
    # Keep the creator UUID as immutable provenance even if the account is removed.
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor_type: Mapped[DraftActorType] = mapped_column(
        Enum(DraftActorType, native_enum=False, values_callable=_enum_values)
    )
    reason: Mapped[DraftRevisionReason] = mapped_column(
        Enum(
            DraftRevisionReason,
            native_enum=False,
            values_callable=_enum_values,
            length=32,
        )
    )
    restored_from_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True
    )
    restored_from_revision_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    referenced_asset_ids: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    compile_status: Mapped[CompileStatus] = mapped_column(
        Enum(CompileStatus, native_enum=False, values_callable=_enum_values),
        default=CompileStatus.PENDING,
    )
    active_compile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    compile_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    compile_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    compiled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(
        back_populates="draft_revisions", foreign_keys=[article_id]
    )


class DraftCommandReceipt(Base):
    __tablename__ = "draft_command_receipts"

    command_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    request_hash: Mapped[str] = mapped_column(String(64))
    base_revision: Mapped[int] = mapped_column(Integer)
    result_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("article_draft_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    result_revision_number: Mapped[int] = mapped_column(Integer)
    affected_block_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


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
        UniqueConstraint(
            "article_version_id", "user_id", name="uq_article_reviewers_version_user"
        ),
        UniqueConstraint(
            "id", "article_version_id", name="uq_article_reviewers_id_version"
        ),
        ForeignKeyConstraint(
            ["article_version_id", "article_id"],
            ["article_versions.id", "article_versions.article_id"],
            name="fk_article_reviewers_version_article",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    article_version_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
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
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_midpoint_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    reminder_due_soon_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
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

    article: Mapped["Article"] = relationship(
        back_populates="reviewer_assignments", foreign_keys=[article_id]
    )
    article_version: Mapped["ArticleVersion"] = relationship(
        foreign_keys=[article_version_id, article_id], overlaps="article"
    )
    user: Mapped["User"] = relationship(back_populates="reviewer_assignments")
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="article_reviewer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "article_reviewer_id", "article_version_id",
            name="uq_reviews_assignment_version",
        ),
        ForeignKeyConstraint(
            ["article_reviewer_id", "article_version_id"],
            ["article_reviewers.id", "article_reviewers.article_version_id"],
            name="fk_reviews_assignment_version",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    article_reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
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
    reveal_reviewer_identity_to_author: Mapped[bool] = mapped_column(
        Boolean, default=False
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