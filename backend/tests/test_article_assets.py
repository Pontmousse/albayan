import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from urllib.parse import quote

from app.core import s3
from app.models.enums import CompileStatus
from app.routers import articles


def test_list_prefix_filters_directories() -> None:
    client = MagicMock()
    client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "articles/x/versions/v1/assets/a.jpg", "Size": 10},
            {"Key": "articles/x/versions/v1/assets/", "Size": 0},
            {"Key": "articles/x/versions/v1/assets/b.png", "Size": 20},
        ],
        "IsTruncated": False,
    }
    with patch.object(s3, "_client", return_value=client), patch.object(
        s3.settings, "s3_bucket", "bucket"
    ):
        rows = s3.list_prefix("articles/x/versions/v1/", "assets")

    assert [row["relative_key"] for row in rows] == ["a.jpg", "b.png"]


def test_delete_bytes_scopes_object_to_version_prefix() -> None:
    client = MagicMock()
    with patch.object(s3, "_client", return_value=client), patch.object(
        s3.settings, "s3_bucket", "bucket"
    ):
        s3.delete_bytes("articles/x/versions/v1/", "assets/photo.jpg")

    client.delete_object.assert_called_once_with(
        Bucket="bucket",
        Key="articles/x/versions/v1/assets/photo.jpg",
    )


def test_list_assets_endpoint_returns_s3_inventory() -> None:
    article_id = uuid.uuid4()
    version = MagicMock()
    version.storage_prefix = "articles/test/versions/v1/"
    actor = MagicMock()
    actor.user_id = uuid.uuid4()
    db = MagicMock()

    listed = [
        {
            "relative_key": "photo.jpg",
            "size": 1024,
            "last_modified": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "content_type": None,
        }
    ]

    with patch.object(articles, "_current_user", return_value=MagicMock()), patch.object(
        articles.article_service, "assert_is_author", return_value=MagicMock()
    ), patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(s3, "list_prefix", return_value=listed):
        payload = articles.list_assets(article_id, MagicMock(), db)

    assert len(payload.assets) == 1
    assert payload.assets[0].asset_id == "assets/photo.jpg"
    assert payload.assets[0].content_type == "image/jpeg"
    assert payload.assets[0].size == 1024


def test_delete_asset_removes_image_and_invalidates_preview() -> None:
    article_id = uuid.uuid4()
    article = MagicMock()
    article.id = article_id
    user = MagicMock()
    user.id = uuid.uuid4()
    version = MagicMock()
    version.storage_prefix = "articles/test/versions/v1/"
    version.compile_status = CompileStatus.SUCCESS
    version.active_compile_id = uuid.uuid4()
    version.compiled_document_hash = "document-hash"
    db = MagicMock()

    with patch.object(articles, "_current_user", return_value=user), patch.object(
        articles.article_service, "assert_is_author", return_value=article
    ), patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(articles.article_service, "assert_draft") as assert_draft, patch.object(
        s3, "delete_bytes"
    ) as delete_bytes:
        articles.delete_asset(article_id, "photo.jpg", MagicMock(), db)

    assert_draft.assert_called_once_with(version)
    delete_bytes.assert_called_once_with(
        "articles/test/versions/v1/",
        "assets/photo.jpg",
    )
    assert version.compile_status == CompileStatus.PENDING
    assert version.active_compile_id is None
    assert version.compiled_document_hash is None
    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_article_pdf_uses_sanitized_utf8_download_filename() -> None:
    article_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.full_name = " أحمد / بن: علي "
    article = MagicMock()
    article.title = " مقاصد * الشريعة? "
    version = MagicMock()
    version.storage_prefix = "articles/test/versions/v3/"
    version.version_number = 3
    db = MagicMock()

    with patch.object(articles, "_current_user", return_value=user), patch.object(
        articles.article_service, "assert_is_author", return_value=article
    ), patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(
        articles.compile_service, "get_compiled_pdf", return_value=b"%PDF-test"
    ):
        response = articles.get_article_pdf(article_id, MagicMock(), db)

    filename = "أحمد_بن_علي_مقاصد_الشريعة_الإصدار_3.pdf"
    assert response.body == b"%PDF-test"
    assert response.headers["content-disposition"] == (
        'inline; filename="article-v3.pdf"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )
