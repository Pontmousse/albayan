"""PostgreSQL integration coverage for immutable formal review rounds."""

import copy
import os
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.article import (
    Article,
    ArticleEditor,
    ArticleReviewer,
    Review,
)
from app.models.enums import (
    ArticleStatus,
    CompileStatus,
    ReviewRecommendation,
    ReviewerAssignmentStatus,
    ReviewStatus,
    InvitationRole,
)
from app.models.user import User
from app.schemas.editor import ReviewerIdentityDisclosure
from app.services import (
    admin_article_service,
    article_draft_service,
    article_service,
    editor_service,
    invitation_service,
)

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not DATABASE_URL.startswith("postgresql"),
    reason="TEST_DATABASE_URL must point to disposable PostgreSQL",
)


def test_v1_revision_request_v2_preserves_round_and_requires_new_assignment():
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    storage: dict[str, object] = {}

    def put_json(key, value):
        assert key not in storage
        storage[key] = copy.deepcopy(value)

    def get_json(prefix):
        return copy.deepcopy(storage.get(f"{prefix}/document.json"))

    def put_bytes(key, body, content_type):
        assert key not in storage
        storage[key] = (body, content_type)

    def get_bytes(prefix, relative):
        value = storage[f"{prefix}/{relative}"]
        assert isinstance(value, tuple)
        return value

    ids: list[uuid.UUID] = []
    article_id: uuid.UUID | None = None
    patches = (
        patch("app.core.s3.put_json_key_immutable", side_effect=put_json),
        patch("app.core.s3.get_json_key", side_effect=lambda key: copy.deepcopy(storage.get(key))),
        patch("app.core.s3.get_json", side_effect=get_json),
        patch("app.core.s3.put_bytes_key_immutable", side_effect=put_bytes),
        patch("app.core.s3.get_bytes", side_effect=get_bytes),
        patch("app.core.s3.assert_exists"),
        patch("app.core.s3.delete_key", side_effect=lambda key: storage.pop(key, None)),
        patch("app.core.s3.delete_prefix"),
        patch("app.services.butex_worker_client.normalize_document", side_effect=lambda value: value),
        patch("app.services.butex_worker_client.export_document", return_value=("tex", [])),
        patch("app.services.email_service.send_submission_received_email"),
        patch("app.services.email_service.send_new_submission_alert_email"),
        patch("app.services.email_service.send_decision_email"),
        patch("app.services.email_service.send_reviewer_assigned_email"),
        patch("app.services.invitation_service.send_invitation_email"),
    )
    for active in patches:
        active.start()
    try:
        with Session(engine, expire_on_commit=False) as db:
            for role in ("author", "editor", "reviewer", "invited"):
                user = User(
                    clerk_id=f"round-{role}-{uuid.uuid4()}",
                    email=f"round-{role}-{uuid.uuid4()}@example.com",
                    full_name=role,
                    affiliation=None,
                    bio=None,
                )
                db.add(user)
                db.flush()
                ids.append(user.id)
            author_id, editor_id, reviewer_id, invited_id = ids
            article = article_service.create_article(db, author_id, "عنوان أول", "ملخص")
            article_id = article.id
            db.add(ArticleEditor(article_id=article.id, user_id=editor_id))
            revision = article_draft_service.get_current_revision(db, article)
            revision.compile_status = CompileStatus.SUCCESS
            revision.active_compile_id = uuid.uuid4()
            revision.compiled_at = datetime.now(UTC)
            storage[
                f"{article_draft_service.preview_prefix(article.id, revision.id, revision.active_compile_id)}/compiled.pdf"
            ] = (b"v1", "application/pdf")
            db.commit()

            v1 = article_service.submit_article(db, article)
            assert v1.version_number == 1
            first_assignment = admin_article_service.assign_reviewer(
                db,
                article.id,
                user_id=reviewer_id,
                review_due_at=datetime.now(UTC) + timedelta(days=7),
            )
            report = Review(
                article_reviewer_id=first_assignment.id,
                article_version_id=v1.id,
                comments_to_author="عدّل الاستنتاج.",
                comments_to_editor="ملاحظة سرية.",
                recommendation=ReviewRecommendation.MAJOR_REVISION,
                status=ReviewStatus.SUBMITTED,
                submitted_at=datetime.now(UTC),
            )
            db.add(report)
            first_assignment.status = ReviewerAssignmentStatus.COMPLETED
            db.commit()

            editor_service.request_revisions(
                db,
                article.id,
                editor_id,
                "يرجى تعديل الاستنتاج.",
                [ReviewerIdentityDisclosure(review_id=report.id, reveal_identity=True)],
            )
            db.refresh(article)
            assert article.status == ArticleStatus.REVISION_REQUESTED
            assert article.revision_requested_for_version_id == v1.id
            opened = article_draft_service.get_current_revision(db, article)
            assert opened.revision_number == 2
            assert opened.compile_status == CompileStatus.PENDING
            db.refresh(report)
            assert report.reveal_reviewer_identity_to_author is True

            editor_service.request_revisions(
                db,
                article.id,
                editor_id,
                "توجيه إداري محدّث.",
                [ReviewerIdentityDisclosure(review_id=report.id, reveal_identity=False)],
                require_editor=False,
            )
            db.refresh(article)
            db.refresh(report)
            assert article.current_draft_revision_id == opened.id
            assert article.revision_request_note == "توجيه إداري محدّث."
            assert report.reveal_reviewer_identity_to_author is False

            opened.compile_status = CompileStatus.SUCCESS
            opened.active_compile_id = uuid.uuid4()
            opened.compiled_at = datetime.now(UTC)
            storage[
                f"{article_draft_service.preview_prefix(article.id, opened.id, opened.active_compile_id)}/compiled.pdf"
            ] = (b"v2", "application/pdf")
            db.commit()
            v2 = article_service.submit_article(db, article)
            assert v2.version_number == 2
            assert v2.storage_prefix.endswith("/versions/v2")
            assert db.scalar(
                select(Review).where(Review.id == report.id)
            ).article_version_id == v1.id
            assert db.scalars(
                select(ArticleReviewer).where(
                    ArticleReviewer.article_version_id == v2.id
                )
            ).all() == []

            second_assignment = admin_article_service.assign_reviewer(
                db,
                article.id,
                user_id=reviewer_id,
                review_due_at=datetime.now(UTC) + timedelta(days=7),
            )
            assert second_assignment.id != first_assignment.id
            assert second_assignment.article_version_id == v2.id

            invited_user = db.get(User, invited_id)
            assert invited_user is not None
            invitation, _ = invitation_service.create_invitation(
                db,
                article_id=article.id,
                role=InvitationRole.REVIEWER,
                email=invited_user.email,
                invited_by=editor_id,
                review_due_at=datetime.now(UTC) + timedelta(days=7),
            )
            assert invitation.article_version_id == v2.id

            editor_service.request_revisions(
                db,
                article.id,
                editor_id,
                "جولة تعديل ثانية.",
                [],
            )
            with pytest.raises(HTTPException) as stale:
                invitation_service.accept_invitation(
                    db, token=invitation.token, user=invited_user
                )
            assert stale.value.status_code == 409

            db.refresh(article)
            third_draft = article_draft_service.get_current_revision(db, article)
            third_draft.compile_status = CompileStatus.SUCCESS
            third_draft.active_compile_id = uuid.uuid4()
            third_draft.compiled_at = datetime.now(UTC)
            storage[
                f"{article_draft_service.preview_prefix(article.id, third_draft.id, third_draft.active_compile_id)}/compiled.pdf"
            ] = (b"v3", "application/pdf")
            db.commit()
            v3 = article_service.submit_article(db, article)
            assert v3.version_number == 3
            assert storage[f"{v1.storage_prefix}/compiled.pdf"][0] == b"v1"
            assert storage[f"{v2.storage_prefix}/compiled.pdf"][0] == b"v2"
    finally:
        for active in reversed(patches):
            active.stop()
        if article_id is not None:
            with Session(engine) as db:
                article = db.get(Article, article_id)
                if article is not None:
                    db.delete(article)
                    db.commit()
                for user_id in ids:
                    user = db.get(User, user_id)
                    if user is not None:
                        db.delete(user)
                db.commit()
        engine.dispose()
