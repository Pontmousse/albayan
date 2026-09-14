from __future__ import annotations

import asyncio
import base64
import inspect
import unittest
import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch

from mcp.server.mcpserver import MCPServer
from mcp.types import ImageContent
from pydantic import TypeAdapter, ValidationError

from albayan_mcp.api_client import BinaryApiResponse
from albayan_mcp.file_download import DownloadedImage
from albayan_mcp.tools.assets import ClientFileInput, register_asset_tools
from tests.test_profile_tools import FakeServer


class AssetToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server = FakeServer()
        register_asset_tools(self.server)
        self.article_id = uuid.uuid4()

    def test_registration_exposes_exact_asset_tools_and_annotations(self) -> None:
        self.assertEqual(
            set(self.server.tools),
            {
                "list_article_assets",
                "get_article_asset",
                "upload_article_asset",
            },
        )
        self.assertTrue(
            self.server.tool_options["list_article_assets"]["annotations"].read_only_hint
        )
        upload = self.server.tool_options["upload_article_asset"]
        self.assertEqual(upload["meta"], {"openai/fileParams": ["file"]})
        self.assertFalse(upload["annotations"].read_only_hint)
        self.assertFalse(upload["annotations"].destructive_hint)
        self.assertFalse(upload["annotations"].idempotent_hint)

    def test_native_file_input_schema_has_exact_openai_shape(self) -> None:
        tool = self.server.tools["upload_article_asset"]
        hints = inspect.get_annotations(tool, eval_str=True)
        schema = TypeAdapter(hints["file"]).json_schema()

        self.assertEqual(
            set(schema["properties"]),
            {"download_url", "file_id", "mime_type", "file_name"},
        )
        self.assertEqual(set(schema["required"]), {"download_url", "file_id"})
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mime_type"]["type"], "string")
        self.assertEqual(schema["properties"]["file_name"]["type"], "string")
        with self.assertRaises(ValidationError):
            ClientFileInput.model_validate(
                {
                    "download_url": "https://files.example/image.png",
                    "file_id": "file-1",
                    "unexpected": True,
                }
            )

    def test_real_discovery_publishes_file_metadata_and_typed_outputs(self) -> None:
        server = MCPServer("asset-schema-test")
        register_asset_tools(server)
        published = {tool.name: tool for tool in asyncio.run(server.list_tools())}

        upload = published["upload_article_asset"]
        self.assertEqual(upload.meta["openai/fileParams"], ["file"])
        file_schema = upload.input_schema["properties"]["file"]
        definition = upload.input_schema["$defs"][
            file_schema["$ref"].rsplit("/", 1)[-1]
        ]
        self.assertEqual(
            set(definition["properties"]),
            {"download_url", "file_id", "mime_type", "file_name"},
        )
        self.assertEqual(set(definition["required"]), {"download_url", "file_id"})
        self.assertEqual(definition["properties"]["mime_type"]["type"], "string")
        self.assertEqual(definition["properties"]["file_name"]["type"], "string")
        self.assertIsNotNone(upload.output_schema)
        self.assertIsNotNone(published["list_article_assets"].output_schema)
        self.assertIsNone(published["get_article_asset"].output_schema)

    async def test_list_assets_returns_typed_metadata(self) -> None:
        updated_at = datetime(2026, 9, 14, tzinfo=UTC).isoformat()
        with patch(
            "albayan_mcp.tools.assets.api_get_object",
            new=AsyncMock(
                return_value={
                    "assets": [
                        {
                            "asset_id": "assets/photo.png",
                            "content_type": "image/png",
                            "size": 123,
                            "updated_at": updated_at,
                        }
                    ]
                }
            ),
        ) as get:
            result = await self.server.tools["list_article_assets"](self.article_id)

        get.assert_awaited_once_with(f"/api/v1/articles/{self.article_id}/assets")
        self.assertEqual(result.assets[0].asset_id, "assets/photo.png")
        self.assertEqual(result.assets[0].size, 123)

    async def test_retrieve_returns_native_image_content(self) -> None:
        response = BinaryApiResponse(
            content=b"png-data",
            content_type="image/png",
            headers={},
        )
        with patch(
            "albayan_mcp.tools.assets.api_get_bytes",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_article_asset"](
                self.article_id,
                "assets/photo.png",
            )

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/assets/photo.png"
        )
        self.assertIsInstance(result, ImageContent)
        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.data, base64.b64encode(b"png-data").decode("ascii"))
        self.assertEqual(result.meta["asset_id"], "assets/photo.png")

    async def test_upload_downloads_native_file_then_forwards_only_to_fastapi(self) -> None:
        downloaded = DownloadedImage(
            content=b"image-bytes",
            content_type="image/webp",
            filename="upload.webp",
        )
        file = ClientFileInput(
            download_url="https://temporary.example/file",
            file_id="file-1",
            mime_type="image/webp",
            file_name="original.webp",
        )
        with patch(
            "albayan_mcp.tools.assets.download_client_image",
            new=AsyncMock(return_value=downloaded),
        ) as download, patch(
            "albayan_mcp.tools.assets.api_post_file_object",
            new=AsyncMock(
                return_value={
                    "asset_id": "assets/generated.webp",
                    "content_type": "image/webp",
                    "size": 11,
                }
            ),
        ) as post:
            result = await self.server.tools["upload_article_asset"](
                self.article_id,
                file,
            )

        download.assert_awaited_once_with(
            file.download_url,
            declared_content_type="image/webp",
        )
        post.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/assets",
            filename="upload.webp",
            content=b"image-bytes",
            content_type="image/webp",
        )
        self.assertEqual(result.asset_id, "assets/generated.webp")


if __name__ == "__main__":
    unittest.main()
