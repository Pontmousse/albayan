"""Typed article-image tools backed exclusively by FastAPI."""

from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import quote

from mcp.server.mcpserver import MCPServer
from mcp.types import ImageContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from albayan_mcp.api_client import (
    api_get_bytes,
    api_get_object,
    api_post_file_object,
)
from albayan_mcp.file_download import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    download_client_image,
)


_ASSET_ID_RE = re.compile(
    r"^assets/([A-Za-z0-9._-]+\.(?:jpg|jpeg|png|gif|webp))$",
    re.IGNORECASE,
)

ArticleId = Annotated[
    uuid.UUID,
    Field(description="Article UUID whose current version owns the image assets."),
]
AssetId = Annotated[
    StrictStr,
    Field(
        min_length=1,
        max_length=262,
        pattern=r"^assets/[A-Za-z0-9._-]+\.(?:jpg|jpeg|png|gif|webp)$",
        description="Stable article-relative image ID returned by FastAPI.",
    ),
]
ImageContentType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class ClientFileInput(BaseModel):
    """ChatGPT native file parameter; its exact shape is part of tool discovery."""

    model_config = ConfigDict(extra="forbid")

    download_url: StrictStr = Field(min_length=1, max_length=4096)
    file_id: StrictStr = Field(min_length=1, max_length=256)
    mime_type: StrictStr = Field(default="", max_length=100)
    file_name: StrictStr = Field(default="", max_length=255)


class ArticleAssetResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: AssetId
    content_type: ImageContentType
    size: int = Field(ge=0)
    updated_at: datetime | None = None


class ArticleAssetsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assets: list[ArticleAssetResult]


class ArticleAssetUploadResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: AssetId
    content_type: ImageContentType
    size: int = Field(ge=1)


def _asset_filename(asset_id: str) -> str:
    match = _ASSET_ID_RE.fullmatch(asset_id)
    if match is None or match.group(1).startswith("."):
        raise ValueError("معرّف الصورة غير صالح.")
    return match.group(1)


def register_asset_tools(server: MCPServer) -> None:
    read_annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
    )

    @server.tool(
        name="list_article_assets",
        title="List article image assets",
        description=(
            "List supported images belonging to the article's current version. Use the "
            "returned stable asset_id values for retrieval or typed Document2 figure "
            "commands; never invent storage paths."
        ),
        annotations=read_annotations,
    )
    async def list_article_assets(article_id: ArticleId) -> ArticleAssetsResult:
        data = await api_get_object(f"/api/v1/articles/{article_id}/assets")
        return ArticleAssetsResult(**data)

    @server.tool(
        name="get_article_asset",
        title="Retrieve an article image asset",
        description=(
            "Retrieve and display one image from the article's current version using an "
            "asset_id returned by list_article_assets. FastAPI authorizes the caller and "
            "never exposes storage credentials or unrestricted object URLs."
        ),
        annotations=read_annotations,
    )
    async def get_article_asset(
        article_id: ArticleId,
        asset_id: AssetId,
    ) -> ImageContent:
        filename = _asset_filename(asset_id)
        response = await api_get_bytes(
            f"/api/v1/articles/{article_id}/assets/{quote(filename, safe='')}"
        )
        if response.content_type not in ALLOWED_IMAGE_TYPES:
            raise RuntimeError("استجابة الأصل ليست صورة مدعومة.")
        if not response.content or len(response.content) > MAX_IMAGE_BYTES:
            raise RuntimeError("حجم استجابة الصورة غير صالح.")
        return ImageContent(
            data=base64.b64encode(response.content).decode("ascii"),
            mimeType=response.content_type,
            _meta={"asset_id": asset_id, "size": len(response.content)},
        )

    @server.tool(
        name="upload_article_asset",
        title="Upload an article image asset",
        description=(
            "Upload one user-selected JPEG, PNG, GIF, or WebP image (maximum 5 MiB) to "
            "the article's current draft. Use the returned asset_id in insert_figure or "
            "update_figure. The file must come from the client's native file picker; do "
            "not invent file bytes or URLs."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        meta={"openai/fileParams": ["file"]},
    )
    async def upload_article_asset(
        article_id: ArticleId,
        file: ClientFileInput,
    ) -> ArticleAssetUploadResult:
        downloaded = await download_client_image(
            file.download_url,
            declared_content_type=file.mime_type or None,
        )
        data = await api_post_file_object(
            f"/api/v1/articles/{article_id}/assets",
            filename=downloaded.filename,
            content=downloaded.content,
            content_type=downloaded.content_type,
        )
        return ArticleAssetUploadResult(**data)
