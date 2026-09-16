import re
import unicodedata
import uuid
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select

from app.core import s3
from app.core.actor import Actor, ActorDep, current_actor_user, require_actor_scope
from app.core.clerk import AuthDep, DbDep
from app.core.config import settings
from app.core.deps import current_user
from app.models.article import ArticleReviewer, ArticleVersion, Review
from app.models.enums import ArticleStatus, ReviewStatus
from app.models.user import User
from app.schemas.article import (
    ArticleAssetRead,
    ArticleAssetUploadRead,
    ArticleAssetsList,
    ArticleCreate,
    ArticleDetail,
    ArticleSummary,
    ArticleUpdate,
    AuthorRevisionFeedback,
    DocumentBlocksRead,
    DocumentCommandPayload,
    DocumentCommandResult,
    DocumentOutlineRead,
    DraftCompileStatusRead,
    DraftRestorePayload,
    DraftRevisionRead,
    DraftRevisionHistoryDetail,
    DraftRevisionHistoryItem,
    DraftUpdatePayload,
    VersionRead,
)
from app.services import article_draft_service, article_service, compile_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_MAX_ASSET_BYTES = 5 * 1024 * 1024
_FILENAME_UNSAFE_RE = re.compile(r'[\x00-\x1f\x7f/\\:*?"<>|]+')
_FILENAME_WHITESPACE_RE = re.compile(r"\s+")
_ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _current_user(auth: AuthDep, db: DbDep):
    return current_user(auth, db)


def _detail(db, article) -> ArticleDetail:
    versions = sorted(article.versions, key=lambda value: value.version_number, reverse=True)
    feedback: list[AuthorRevisionFeedback] = []
    if (
        article.status == ArticleStatus.REVISION_REQUESTED
        and article.revision_requested_for_version_id is not None
    ):
        rows = db.execute(
            select(Review, User.full_name)
            .join(
                ArticleReviewer,
                ArticleReviewer.id == Review.article_reviewer_id,
            )
            .join(User, User.id == ArticleReviewer.user_id)
            .where(
                Review.article_version_id == article.revision_requested_for_version_id,
                Review.status == ReviewStatus.SUBMITTED,
                Review.comments_to_author.is_not(None),
            )
            .order_by(Review.submitted_at, Review.id)
        ).all()
        visible_index = 0
        for review, reviewer_name in rows:
            comments = (review.comments_to_author or "").strip()
            if not comments:
                continue
            visible_index += 1
            anonymous_label = f"المراجع {str(visible_index).translate(_ARABIC_DIGITS)}"
            feedback.append(
                AuthorRevisionFeedback(
                    review_id=review.id,
                    reviewer_label=(
                        reviewer_name or anonymous_label
                        if review.reveal_reviewer_identity_to_author
                        else anonymous_label
                    ),
                    comments_to_author=comments,
                    recommendation=review.recommendation,
                )
            )
    return ArticleDetail(
        id=article.id,
        title=article.title,
        abstract=article.abstract,
        status=article.status,
        current_draft_revision_id=article.current_draft_revision_id,
        draft_revision_number=article.draft_revision_number,
        created_at=article.created_at,
        updated_at=article.updated_at,
        revision_request_note=article.revision_request_note,
        revision_requested_for_version_id=article.revision_requested_for_version_id,
        revision_requested_at=article.revision_requested_at,
        revision_feedback=feedback,
        latest_version=VersionRead.model_validate(versions[0]) if versions else None,
        versions=[VersionRead.model_validate(version) for version in versions],
    )


def _sanitize_download_filename_part(value: str | None, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    cleaned = _FILENAME_UNSAFE_RE.sub("", normalized)
    cleaned = _FILENAME_WHITESPACE_RE.sub("_", cleaned).strip(" ._")
    return cleaned[:80].rstrip(" ._") or fallback


def _pdf_headers(user_name: str | None, title: str, version_number: int) -> dict[str, str]:
    author = _sanitize_download_filename_part(user_name, "المؤلف")
    article = _sanitize_download_filename_part(title, "المقال")
    filename = f"{author}_{article}_الإصدار_{version_number}.pdf"
    encoded = quote(filename, safe="")
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Content-Disposition": (
            f'inline; filename="article-v{version_number}.pdf"; filename*=UTF-8\'\'{encoded}'
        ),
    }


def _guess_image_content_type(asset_id: str) -> str | None:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(PurePosixPath(asset_id).suffix.lower())


def _validate_asset_filename(filename: str) -> tuple[str, str]:
    name = PurePosixPath(filename).name
    if (
        name != filename
        or not name
        or len(name) > 255
        or name in (".", "..")
        or name.startswith(".")
        or not re.fullmatch(r"[A-Za-z0-9._-]+", name)
    ):
        raise HTTPException(status_code=400, detail="معرّف الصورة غير صالح.")
    content_type = _guess_image_content_type(name)
    if content_type is None:
        raise HTTPException(status_code=400, detail="نوع ملف الصورة غير صالح.")
    return name, content_type


def _formal_version(db: DbDep, article_id: uuid.UUID, version_id: uuid.UUID) -> ArticleVersion:
    version = db.get(ArticleVersion, version_id)
    if version is None or version.article_id != article_id:
        raise HTTPException(status_code=404, detail="الإصدار غير موجود.")
    return version


@router.get("/me", response_model=list[ArticleSummary])
def list_my_articles(actor: ActorDep, db: DbDep) -> list[ArticleSummary]:
    require_actor_scope(actor, "articles:read")
    rows = article_service.list_articles_for_author(db, actor.user_id)
    return [
        ArticleSummary(
            id=article.id,
            title=article.title,
            status=article.status,
            latest_version_number=version.version_number if version else None,
            updated_at=article.updated_at,
            submitted_at=version.submitted_at if version else None,
        )
        for article, version in rows
    ]


@router.post("", response_model=ArticleDetail, status_code=201)
def create_article(payload: ArticleCreate, actor: ActorDep, db: DbDep) -> ArticleDetail:
    require_actor_scope(actor, "articles:draft:write")
    article = article_service.create_article(db, actor.user_id, payload.title, payload.abstract)
    return _detail(db, article)


@router.get("/{article_id}", response_model=ArticleDetail)
def get_article(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> ArticleDetail:
    require_actor_scope(actor, "articles:read")
    article = article_service.assert_is_author(db, article_id, actor.user_id)
    return _detail(db, article)


@router.patch("/{article_id}", response_model=ArticleDetail)
def update_article(
    article_id: uuid.UUID, payload: ArticleUpdate, actor: ActorDep, db: DbDep
) -> ArticleDetail:
    require_actor_scope(actor, "articles:draft:write")
    article = article_draft_service.patch_metadata(db, article_id, actor, payload)
    return _detail(db, article)


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, auth: AuthDep, db: DbDep) -> None:
    user = _current_user(auth, db)
    article_service.delete_draft_article(db, article_id, user.id)


@router.get("/{article_id}/draft", response_model=DraftRevisionRead)
def get_draft(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.get_draft(db, article_id, actor)


@router.put("/{article_id}/draft", response_model=DraftRevisionRead)
def put_draft(
    article_id: uuid.UUID, payload: DraftUpdatePayload, actor: ActorDep, db: DbDep
) -> dict:
    require_actor_scope(actor, "articles:draft:write")
    return article_draft_service.put_draft(
        db, article_id, actor, payload.base_revision, payload.document
    )


@router.get("/{article_id}/draft/outline", response_model=DocumentOutlineRead)
def get_draft_outline(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.get_outline(db, article_id, actor)


@router.get("/{article_id}/draft/blocks", response_model=DocumentBlocksRead)
def get_draft_blocks(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.get_blocks(db, article_id, actor)


@router.get(
    "/{article_id}/draft/revisions",
    response_model=list[DraftRevisionHistoryItem],
)
def list_draft_revisions(
    article_id: uuid.UUID, actor: ActorDep, db: DbDep
) -> list[dict]:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.list_revision_history(db, article_id, actor)


@router.get(
    "/{article_id}/draft/revisions/{revision_id}",
    response_model=DraftRevisionHistoryDetail,
)
def get_draft_revision(
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    actor: ActorDep,
    db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.get_revision_history_detail(
        db, article_id, revision_id, actor
    )


@router.post(
    "/{article_id}/draft/revisions/{revision_id}/restore",
    response_model=DraftRevisionRead,
)
def restore_draft_revision(
    article_id: uuid.UUID,
    revision_id: uuid.UUID,
    payload: DraftRestorePayload,
    auth: AuthDep,
    db: DbDep,
) -> dict:
    user = _current_user(auth, db)
    actor = Actor(
        user_id=user.id,
        clerk_id=user.clerk_id,
        auth_method="human",
    )
    return article_draft_service.restore_revision(
        db,
        article_id,
        revision_id,
        actor,
        payload.base_revision,
    )


@router.post("/{article_id}/draft/commands", response_model=DocumentCommandResult)
def apply_draft_command(
    article_id: uuid.UUID,
    payload: DocumentCommandPayload,
    actor: ActorDep,
    db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:draft:write")
    return article_draft_service.apply_command(db, article_id, actor, payload)


@router.post(
    "/{article_id}/draft/compile", response_model=DraftCompileStatusRead, status_code=202
)
def compile_draft(
    article_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    actor: ActorDep,
    db: DbDep,
) -> dict:
    require_actor_scope(actor, "articles:draft:write")
    status, task_args = article_draft_service.prepare_compile(db, article_id, actor)
    background_tasks.add_task(compile_service.schedule_compile, *task_args)
    return status


@router.get("/{article_id}/draft/compile/status", response_model=DraftCompileStatusRead)
def get_draft_compile_status(
    article_id: uuid.UUID, actor: ActorDep, db: DbDep
) -> dict:
    require_actor_scope(actor, "articles:read")
    return article_draft_service.compile_status(db, article_id, actor)


@router.get("/{article_id}/draft/pdf")
def get_draft_pdf(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> Response:
    require_actor_scope(actor, "articles:read")
    article = article_service.assert_is_author(db, article_id, actor.user_id)
    user = current_actor_user(actor, db)
    body = article_draft_service.get_current_pdf(db, article_id, actor)
    response = Response(
        content=body,
        media_type="application/pdf",
        headers=_pdf_headers(user.full_name, article.title, article.draft_revision_number),
    )
    response.headers["X-Albayan-Draft-Revision"] = str(article.draft_revision_number)
    response.headers["X-Albayan-Compile-Id"] = str(
        article_draft_service.get_current_revision(db, article).active_compile_id
    )
    return response


@router.get("/{article_id}/draft/compile/log")
def get_draft_compile_log(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> dict[str, str]:
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")
    require_actor_scope(actor, "articles:read")
    return {"log": article_draft_service.get_current_compile_log(db, article_id, actor)}


@router.get("/{article_id}/assets", response_model=ArticleAssetsList)
def list_assets(article_id: uuid.UUID, actor: ActorDep, db: DbDep) -> ArticleAssetsList:
    require_actor_scope(actor, "articles:read")
    article_service.assert_is_author(db, article_id, actor.user_id)
    rows = s3.list_prefix(article_draft_service.draft_asset_prefix(article_id), "assets")
    assets: list[ArticleAssetRead] = []
    for row in rows:
        try:
            filename, guessed = _validate_asset_filename(row["relative_key"])
        except HTTPException:
            continue
        content_type = (row["content_type"] or "").split(";", 1)[0].lower()
        assets.append(
            ArticleAssetRead(
                asset_id=f"assets/{filename}",
                content_type=content_type if content_type in _ALLOWED_IMAGE_TYPES else guessed,
                size=row["size"],
                updated_at=row["last_modified"],
            )
        )
    assets.sort(key=lambda item: item.updated_at.timestamp() if item.updated_at else 0, reverse=True)
    return ArticleAssetsList(assets=assets)


@router.post("/{article_id}/assets", response_model=ArticleAssetUploadRead)
async def upload_asset(
    article_id: uuid.UUID,
    actor: ActorDep,
    db: DbDep,
    file: UploadFile = File(...),
) -> ArticleAssetUploadRead:
    require_actor_scope(actor, "articles:draft:write")
    article_draft_service.assert_editable_author(db, article_id, actor)
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    ext = _ALLOWED_IMAGE_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم. استخدم صورة JPEG أو PNG أو GIF أو WebP.")
    body = await file.read()
    if not body:
        raise HTTPException(status_code=400, detail="الملف فارغ.")
    if len(body) > _MAX_ASSET_BYTES:
        raise HTTPException(status_code=400, detail="حجم الصورة يتجاوز الحد المسموح.")
    asset_id = f"assets/{uuid.uuid4().hex}{ext}"
    s3.put_bytes_key_immutable(
        f"{article_draft_service.draft_asset_prefix(article_id)}/{asset_id}",
        body,
        content_type,
    )
    return ArticleAssetUploadRead(asset_id=asset_id, content_type=content_type, size=len(body))


@router.delete("/{article_id}/assets/{filename}", status_code=204)
def delete_asset(
    article_id: uuid.UUID, filename: str, actor: ActorDep, db: DbDep
) -> None:
    require_actor_scope(actor, "articles:draft:write")
    name, _ = _validate_asset_filename(filename)
    article_draft_service.assert_editable_author(db, article_id, actor)
    asset_id = f"assets/{name}"
    if article_draft_service.asset_is_referenced_by_history(
        db, article_id, asset_id
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "لا يمكن حذف صورة مستخدمة في سجل المسودة المحتفظ به. "
                "أزلها من المراجعات الحالية وانتظر خروج المراجعات القديمة من السجل."
            ),
        )
    s3.delete_key(f"{article_draft_service.draft_asset_prefix(article_id)}/{asset_id}")


@router.get("/{article_id}/assets/{filename}")
def get_asset(
    article_id: uuid.UUID, filename: str, actor: ActorDep, db: DbDep
) -> Response:
    require_actor_scope(actor, "articles:read")
    name, guessed = _validate_asset_filename(filename)
    article_service.assert_is_author(db, article_id, actor.user_id)
    body, content_type = s3.get_bytes(
        article_draft_service.draft_asset_prefix(article_id), f"assets/{name}"
    )
    normalized = (content_type or "").split(";", 1)[0].lower()
    return Response(
        content=body,
        media_type=normalized if normalized in _ALLOWED_IMAGE_TYPES else guessed,
        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/{article_id}/versions/{version_id}/document")
def get_version_document(
    article_id: uuid.UUID, version_id: uuid.UUID, actor: ActorDep, db: DbDep
) -> dict:
    require_actor_scope(actor, "articles:read")
    article_service.assert_is_author(db, article_id, actor.user_id)
    version = _formal_version(db, article_id, version_id)
    return {"document": s3.get_json(version.storage_prefix)}


@router.get("/{article_id}/versions/{version_id}/pdf")
def get_version_pdf(
    article_id: uuid.UUID, version_id: uuid.UUID, actor: ActorDep, db: DbDep
) -> Response:
    require_actor_scope(actor, "articles:read")
    article = article_service.assert_is_author(db, article_id, actor.user_id)
    version = _formal_version(db, article_id, version_id)
    user = current_actor_user(actor, db)
    return Response(
        content=compile_service.get_compiled_pdf(version.storage_prefix),
        media_type="application/pdf",
        headers=_pdf_headers(user.full_name, version.title_snapshot or article.title, version.version_number),
    )


@router.get("/{article_id}/versions/{version_id}/assets/{filename}")
def get_version_asset(
    article_id: uuid.UUID,
    version_id: uuid.UUID,
    filename: str,
    actor: ActorDep,
    db: DbDep,
) -> Response:
    require_actor_scope(actor, "articles:read")
    article_service.assert_is_author(db, article_id, actor.user_id)
    version = _formal_version(db, article_id, version_id)
    name, guessed = _validate_asset_filename(filename)
    body, content_type = s3.get_bytes(version.storage_prefix, f"assets/{name}")
    normalized = (content_type or "").split(";", 1)[0].lower()
    return Response(content=body, media_type=normalized if normalized in _ALLOWED_IMAGE_TYPES else guessed)


@router.post("/{article_id}/submit", response_model=ArticleDetail)
def submit_article(article_id: uuid.UUID, auth: AuthDep, db: DbDep) -> ArticleDetail:
    user = _current_user(auth, db)
    article = article_service.assert_is_author(db, article_id, user.id)
    article_service.submit_article(db, article)
    db.refresh(article)
    return _detail(db, article)
