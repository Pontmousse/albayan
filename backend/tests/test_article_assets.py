import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.core import s3
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
