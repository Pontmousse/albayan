import uuid
from pathlib import PurePosixPath

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, update

from app.models.article import Article

from app.core import s3
from app.core.clerk import AuthDep, DbDep
from app.core.config import settings
from app.core.deps import current_user
from app.schemas.article import (
    ArticleCreate,
    ArticleDetail,
    ArticleSummary,
    ArticleUpdate,
    CompilePayload,
    DocumentPayload,
    VersionRead,
)
from app.services import article_service, compile_service

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_MAX_ASSET_BYTES = 5 * 1024 * 1024


def _current_user(auth: AuthDep, db: DbDep):
    return current_user(auth, db)


def _detail(db, article) -> ArticleDetail:
    versions = sorted(article.versions, key=lambda v: v.version_number, reverse=True)
    return ArticleDetail(
        id=article.id,
        title=article.title,
        abstract=article.abstract,
        created_at=article.created_at,
        updated_at=article.updated_at,
        current_version=VersionRead.model_validate(versions[0]),
        versions=[VersionRead.model_validate(v) for v in versions],
    )


@router.get("/me", response_model=list[ArticleSummary])
def list_my_articles(auth: AuthDep, db: DbDep) -> list[ArticleSummary]:
    user = _current_user(auth, db)
    rows = article_service.list_articles_for_author(db, user.id)
    return [
        ArticleSummary(
            id=article.id,
            title=article.title,
            status=version.status,
            version_number=version.version_number,
            updated_at=article.updated_at,
            submitted_at=version.submitted_at,
        )
        for article, version in rows
    ]


@router.post("", response_model=ArticleDetail, status_code=201)
def create_article(payload: ArticleCreate, auth: AuthDep, db: DbDep) -> ArticleDetail:
    user = _current_user(auth, db)
    article = article_service.create_article(db, user.id, payload.title, payload.abstract)
    return _detail(db, article)


@router.get("/{article_id}", response_model=ArticleDetail)
def get_article(article_id: uuid.UUID, auth: AuthDep, db: DbDep) -> ArticleDetail:
    user = _current_user(auth, db)
    article = article_service.assert_is_author(db, article_id, user.id)
    return _detail(db, article)


@router.patch("/{article_id}", response_model=ArticleDetail)
def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    auth: AuthDep,
    db: DbDep,
) -> ArticleDetail:
    user = _current_user(auth, db)
    article = article_service.assert_is_author(db, article_id, user.id)
    article = article_service.update_draft_metadata(
        db, article, payload.title, payload.abstract
    )
    return _detail(db, article)


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, auth: AuthDep, db: DbDep) -> None:
    """يحذف مسودة المؤلف مع المخطوطة والأصول وملف المعاينة."""
    user = _current_user(auth, db)
    article_service.delete_draft_article(db, article_id, user.id)


@router.get("/{article_id}/document")
def get_document(article_id: uuid.UUID, auth: AuthDep, db: DbDep) -> dict:
    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    document = s3.get_json(version.storage_prefix)
    return {"document": document}


@router.put("/{article_id}/document")
def save_document(
    article_id: uuid.UUID, payload: DocumentPayload, auth: AuthDep, db: DbDep
) -> dict:
    user = _current_user(auth, db)
    article = article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    article_service.assert_draft(version)
    s3.put_json(version.storage_prefix, payload.document)
    # نلمس updated_at ليعكس «آخر تحديث» في القائمة
    db.execute(
        update(Article).where(Article.id == article.id).values(updated_at=func.now())
    )
    db.commit()
    return {"ok": True}


@router.post("/{article_id}/assets")
async def upload_asset(
    article_id: uuid.UUID,
    auth: AuthDep,
    db: DbDep,
    file: UploadFile = File(...),
) -> dict:
    """يرفع صورة تحت storage_prefix/assets/ — مسودة فقط."""
    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    article_service.assert_draft(version)

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    ext = _ALLOWED_IMAGE_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مدعوم. استخدم JPEG أو PNG أو GIF أو WebP.",
        )

    body = await file.read()
    if not body:
        raise HTTPException(status_code=400, detail="الملف فارغ.")
    if len(body) > _MAX_ASSET_BYTES:
        raise HTTPException(
            status_code=400,
            detail="حجم الصورة يتجاوز الحد المسموح (5 ميغابايت).",
        )

    asset_id = f"assets/{uuid.uuid4().hex}{ext}"
    s3.put_bytes(version.storage_prefix, asset_id, body, content_type)
    return {"asset_id": asset_id, "content_type": content_type}


@router.get("/{article_id}/assets/{filename}")
def get_asset(
    article_id: uuid.UUID,
    filename: str,
    auth: AuthDep,
    db: DbDep,
) -> Response:
    """يبث صورة أصل من storage_prefix/assets/{filename}."""
    name = PurePosixPath(filename).name
    if name != filename or not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="اسم ملف غير صالح.")

    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)

    relative_key = f"assets/{name}"
    body, content_type = s3.get_bytes(version.storage_prefix, relative_key)
    return Response(
        content=body,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.post("/{article_id}/compile", response_model=VersionRead)
def compile_article(
    article_id: uuid.UUID,
    payload: CompilePayload,
    background_tasks: BackgroundTasks,
    auth: AuthDep,
    db: DbDep,
) -> VersionRead:
    """يبدأ إنشاء ملفّ المعاينة — LaTeX من الواجهة، الأصول من S3."""
    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    asset_keys = compile_service.validate_asset_keys(payload.asset_keys)
    version, compile_id = compile_service.begin_compile(
        db, version, payload.document_hash
    )
    background_tasks.add_task(
        compile_service.schedule_compile,
        version.id,
        compile_id,
        payload.latex,
        asset_keys,
        payload.document_hash,
    )
    return VersionRead.model_validate(version)


@router.get("/{article_id}/pdf")
def get_article_pdf(
    article_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> Response:
    """يبث compiled.pdf للإصدار الحالي."""
    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    body = compile_service.get_compiled_pdf(version.storage_prefix)
    return Response(
        content=body,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, max-age=60",
            "Content-Disposition": 'inline; filename="compiled.pdf"',
        },
    )


@router.get("/{article_id}/compile-log")
def get_article_compile_log(
    article_id: uuid.UUID, auth: AuthDep, db: DbDep
) -> dict[str, str]:
    """يرجع compile.log — متاح فقط عند DEV_MODE=true."""
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="غير موجود.")
    user = _current_user(auth, db)
    article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    log = compile_service.get_compile_log(version.storage_prefix)
    return {"log": log}


@router.post("/{article_id}/submit", response_model=VersionRead)
def submit_article(
    article_id: uuid.UUID,
    auth: AuthDep,
    db: DbDep,
) -> VersionRead:
    user = _current_user(auth, db)
    article = article_service.assert_is_author(db, article_id, user.id)
    version = article_service.current_version(db, article_id)
    article_service.assert_draft(version)
    article_service.assert_document_metadata_matches(article, version)
    compile_service.assert_fresh_preview_for_submit(version)
    version = article_service.submit_article(db, article)
    return VersionRead.model_validate(version)
