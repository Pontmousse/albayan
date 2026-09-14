import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from urllib.parse import quote

import pytest
from fastapi import HTTPException

from app.core import s3
from app.models.enums import CompileStatus
from app.routers import articles
from app.services import compile_service


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
    ), patch.object(s3, "get_json", return_value=None):
        s3.delete_bytes("articles/x/versions/v1/", "assets/photo.jpg")

    client.delete_object.assert_called_once_with(
        Bucket="bucket",
        Key="articles/x/versions/v1/assets/photo.jpg",
    )


def test_assert_exists_uses_head_without_loading_asset() -> None:
    client = MagicMock()
    with patch.object(s3, "_client", return_value=client), patch.object(
        s3.settings, "s3_bucket", "bucket"
    ):
        s3.assert_exists("articles/x/versions/v1/", "assets/photo.jpg")

    client.head_object.assert_called_once_with(
        Bucket="bucket",
        Key="articles/x/versions/v1/assets/photo.jpg",
    )


def test_delete_bytes_rejects_asset_referenced_in_nested_document() -> None:
    document = {
        "blocks": [
            {
                "kind": "section",
                "children": [
                    {
                        "kind": "list",
                        "items": [
                            {
                                "blocks": [
                                    {
                                        "kind": "image",
                                        "assetId": "assets/photo.jpg",
                                        "value": "assets/photo.jpg",
                                    }
                                ]
                            }
                        ],
                    }
                ],
            }
        ]
    }

    with patch.object(s3, "get_json", return_value=document), patch.object(
        s3, "delete_key"
    ) as delete_key:
        with pytest.raises(HTTPException) as exc_info:
            s3.delete_bytes("articles/x/versions/v1/", "assets/photo.jpg")

    assert exc_info.value.status_code == 409
    assert "مستخدمة داخل المقال" in str(exc_info.value.detail)
    delete_key.assert_not_called()


def test_delete_bytes_allows_unreferenced_asset() -> None:
    document = {
        "blocks": [
            {
                "kind": "image",
                "assetId": "assets/other.jpg",
                "value": "assets/other.jpg",
            }
        ]
    }

    with patch.object(s3, "get_json", return_value=document), patch.object(
        s3, "delete_key"
    ) as delete_key:
        s3.delete_bytes("articles/x/versions/v1/", "assets/photo.jpg")

    delete_key.assert_called_once_with("articles/x/versions/v1/assets/photo.jpg")


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

    with patch.object(
        articles.article_service, "assert_is_author", return_value=MagicMock()
    ) as assert_author, patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(s3, "list_prefix", return_value=listed):
        payload = articles.list_assets(article_id, actor, db)

    assert len(payload.assets) == 1
    assert payload.assets[0].asset_id == "assets/photo.jpg"
    assert payload.assets[0].content_type == "image/jpeg"
    assert payload.assets[0].size == 1024
    assert_author.assert_called_once_with(db, article_id, actor.user_id)


@pytest.mark.parametrize(
    "filename",
    [
        "../photo.png",
        "folder/photo.png",
        ".hidden.png",
        "photo.svg",
        "photo space.png",
        "",
    ],
)
def test_asset_filename_validation_rejects_unsafe_or_unsupported_values(
    filename: str,
) -> None:
    with pytest.raises(HTTPException) as raised:
        articles._validate_asset_filename(filename)

    assert raised.value.status_code == 400


def test_get_asset_is_agent_safe_and_returns_supported_mime() -> None:
    article_id = uuid.uuid4()
    actor = MagicMock(user_id=uuid.uuid4())
    version = MagicMock(storage_prefix="articles/test/versions/v1/")
    db = MagicMock()
    with patch.object(
        articles.article_service, "assert_is_author"
    ) as assert_author, patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(
        s3,
        "get_bytes",
        return_value=(b"image-data", "application/octet-stream"),
    ):
        response = articles.get_asset(article_id, "photo.png", actor, db)

    assert response.body == b"image-data"
    assert response.media_type == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert_author.assert_called_once_with(db, article_id, actor.user_id)


class _TestUploadFile:
    def __init__(self, body: bytes, content_type: str) -> None:
        self._body = body
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._body


def _upload_file(body: bytes, content_type: str) -> _TestUploadFile:
    return _TestUploadFile(body, content_type)


def test_upload_asset_accepts_agent_image_and_returns_typed_metadata() -> None:
    article_id = uuid.uuid4()
    actor = MagicMock(user_id=uuid.uuid4())
    version = MagicMock(storage_prefix="articles/test/versions/v1/")
    db = MagicMock()
    with patch.object(
        articles.article_service, "assert_is_author"
    ) as assert_author, patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(
        articles.article_service, "assert_draft"
    ) as assert_draft, patch.object(
        s3, "put_bytes"
    ) as put_bytes:
        result = asyncio.run(
            articles.upload_asset(
                article_id,
                actor,
                db,
                _upload_file(b"png-data", "image/png"),
            )
        )

    assert result.asset_id.startswith("assets/")
    assert result.asset_id.endswith(".png")
    assert result.content_type == "image/png"
    assert result.size == 8
    assert compile_service.validate_asset_keys([result.asset_id]) == [result.asset_id]
    assert_author.assert_called_once_with(db, article_id, actor.user_id)
    assert_draft.assert_called_once_with(version)
    put_bytes.assert_called_once_with(
        version.storage_prefix,
        result.asset_id,
        b"png-data",
        "image/png",
    )


@pytest.mark.parametrize(
    ("body", "content_type", "expected_message"),
    [
        (b"", "image/png", "الملف فارغ"),
        (b"x", "image/svg+xml", "نوع الملف غير مدعوم"),
        (b"x" * (5 * 1024 * 1024 + 1), "image/webp", "حجم الصورة"),
    ],
)
def test_upload_asset_rejects_invalid_file_before_storage_write(
    body: bytes,
    content_type: str,
    expected_message: str,
) -> None:
    article_id = uuid.uuid4()
    actor = MagicMock(user_id=uuid.uuid4())
    version = MagicMock(storage_prefix="articles/test/versions/v1/")
    with patch.object(
        articles.article_service, "assert_is_author"
    ), patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(
        articles.article_service, "assert_draft"
    ), patch.object(
        s3, "put_bytes"
    ) as put_bytes, pytest.raises(HTTPException) as raised:
        asyncio.run(
            articles.upload_asset(
                article_id,
                actor,
                MagicMock(),
                _upload_file(body, content_type),
            )
        )

    assert expected_message in str(raised.value.detail)
    put_bytes.assert_not_called()


def test_non_author_is_rejected_before_asset_storage_access() -> None:
    article_id = uuid.uuid4()
    actor = MagicMock(user_id=uuid.uuid4())
    forbidden = HTTPException(status_code=403, detail="ليست لديك صلاحية.")
    with patch.object(
        articles.article_service, "assert_is_author", side_effect=forbidden
    ), patch.object(s3, "list_prefix") as list_prefix, pytest.raises(
        HTTPException
    ) as raised:
        articles.list_assets(article_id, actor, MagicMock())

    assert raised.value is forbidden
    list_prefix.assert_not_called()


def test_upload_asset_rejects_non_draft_before_reading_or_writing_file() -> None:
    article_id = uuid.uuid4()
    actor = MagicMock(user_id=uuid.uuid4())
    version = MagicMock()
    not_draft = HTTPException(status_code=409, detail="ليست مسودة")
    file = MagicMock()
    file.read = MagicMock()
    with patch.object(
        articles.article_service, "assert_is_author"
    ), patch.object(
        articles.article_service, "current_version", return_value=version
    ), patch.object(
        articles.article_service, "assert_draft", side_effect=not_draft
    ), patch.object(
        s3, "put_bytes"
    ) as put_bytes, pytest.raises(HTTPException) as raised:
        asyncio.run(articles.upload_asset(article_id, actor, MagicMock(), file))

    assert raised.value is not_draft
    file.read.assert_not_called()
    put_bytes.assert_not_called()


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
