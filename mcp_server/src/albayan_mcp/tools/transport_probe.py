"""Self-contained MCP transport diagnostics for ChatGPT/Inspector interoperability.

This module deliberately does not call FastAPI, object storage, or the compiler. It
uses tiny deterministic fixtures so a client can test how MCP content blocks and
OpenAI file parameters survive the MCP bridge in isolation.
"""

from __future__ import annotations

import base64
import json
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from mcp.server.mcpserver import MCPServer
from mcp.types import (
    BlobResourceContents,
    EmbeddedResource,
    ImageContent,
    TextContent,
    TextResourceContents,
    ToolAnnotations,
)
from pydantic import BaseModel, ConfigDict, Field, StrictStr


# A deterministic 2 x 2 RGBA PNG (red/green/blue/white), 75 bytes.
# Keeping it inline makes the diagnostic independent of package-data rules and all
# network/storage services while still exercising real binary MCP content.
_TEST_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEklEQVR4nGP4z8DwHwyBNBgAAEnICff5q7YNAAAAAElFTkSuQmCC"
)

# A deterministic one-page PDF containing the text "Al-Bayan MCP transport probe",
# 608 bytes. It is a complete PDF with a valid xref/trailer and no external assets.
_TEST_PDF_BASE64 = (
    "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAzMDAgMTQ0XSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgNSAwIFIgPj4gPj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA1OCA+PgpzdHJlYW0KQlQgL0YxIDE4IFRmIDM2IDkwIFRkIChBbC1CYXlhbiBNQ1AgdHJhbnNwb3J0IHByb2JlKSBUaiBFVAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+CmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA2NCAwMDAwMCBuIAowMDAwMDAwMTIxIDAwMDAwIG4gCjAwMDAwMDAyNDcgMDAwMDAgbiAKMDAwMDAwMDM1NSAwMDAwMCBuIAp0cmFpbGVyCjw8IC9TaXplIDYgL1Jvb3QgMSAwIFIgPj4Kc3RhcnR4cmVmCjQyNQolJUVPRgo="
)

_TEST_BINARY = b"\x00\x01Al-Bayan-MCP\xfe\xff"

ProbeCase = Literal[
    "image_content",
    "image_content_with_text",
    "embedded_text",
    "embedded_binary",
    "embedded_png",
    "embedded_pdf",
    "embedded_pdf_with_text",
    "upload_file_params",
]

ProbeCaseArg = Annotated[
    ProbeCase,
    Field(
        description=(
            "Transport experiment to run. image_content mirrors get_article_asset; "
            "embedded_pdf mirrors get_article_pdf. The *_with_text cases test whether "
            "a leading TextContent changes ChatGPT behavior. upload_file_params inspects "
            "the client-provided file binding without downloading it."
        )
    ),
]


class DiagnosticFileInput(BaseModel):
    """Permissive probe shape covering both web and reported mobile fileParams forms."""

    model_config = ConfigDict(extra="allow")

    download_url: StrictStr | None = None
    file_id: StrictStr | None = None
    mime_type: StrictStr | None = None
    file_name: StrictStr | None = None
    name: StrictStr | None = None
    size: int | None = None


ProbeFileItem = DiagnosticFileInput | StrictStr
ProbeFilesArg = Annotated[
    list[ProbeFileItem] | None,
    Field(
        description=(
            "Optional ChatGPT-native file binding used only with case=upload_file_params. "
            "The permissive schema accepts the normal web object as well as reported "
            "mobile chat_upload string references."
        ),
    ),
]

ProbeContent = TextContent | ImageContent | EmbeddedResource


def _embedded_blob(*, uri: str, mime_type: str, blob: str, case: str, size: int) -> EmbeddedResource:
    return EmbeddedResource(
        type="resource",
        resource=BlobResourceContents(
            uri=uri,
            mime_type=mime_type,
            blob=blob,
        ),
        _meta={"probe_case": case, "fixture_bytes": size},
    )


def _safe_upload_summary(files: list[ProbeFileItem] | None) -> str:
    """Describe binding shape without echoing URLs, file IDs, or other opaque secrets."""

    items: list[dict[str, Any]] = []
    for raw_item in files or []:
        if isinstance(raw_item, str):
            scheme = raw_item.split("://", 1)[0] if "://" in raw_item else None
            items.append(
                {
                    "kind": "string",
                    "length": len(raw_item),
                    "chat_upload_reference": (
                        raw_item == "chat_upload" or scheme == "chat_upload"
                    ),
                    "scheme": scheme if scheme in {"chat_upload"} else None,
                }
            )
            continue

        item = (
            DiagnosticFileInput.model_validate(raw_item)
            if isinstance(raw_item, dict)
            else raw_item
        )
        download_scheme: str | None = None
        if item.download_url:
            try:
                candidate = urlsplit(item.download_url).scheme.lower()
                download_scheme = candidate if candidate in {"http", "https"} else "other"
            except ValueError:
                download_scheme = "invalid"
        known = {
            "download_url",
            "file_id",
            "mime_type",
            "file_name",
            "name",
            "size",
        }
        extra_keys = sorted((item.model_extra or {}).keys())
        items.append(
            {
                "kind": "object",
                "has_download_url": bool(item.download_url),
                "download_url_scheme": download_scheme,
                "has_file_id": bool(item.file_id),
                "mime_type": item.mime_type,
                "has_file_name": bool(item.file_name or item.name),
                "has_size": item.size is not None,
                "extra_keys": [key for key in extra_keys if key not in known],
            }
        )

    return json.dumps(
        {
            "probe_case": "upload_file_params",
            "received_count": len(items),
            "items": items,
            "note": "No file was downloaded and no URL/file_id value is echoed.",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def register_transport_probe_tool(server: MCPServer) -> None:
    """Register one intentionally isolated diagnostic tool."""

    @server.tool(
        name="test_mcp_content_transport",
        title="Test MCP binary/file transport",
        description=(
            "Diagnostic only. Test how this MCP client transports fixed image/PDF/text/binary "
            "content or OpenAI native fileParams. It never calls FastAPI, storage, or the "
            "compiler. Choose one case per call and report exactly what content the client/model "
            "can see or surface."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
        meta={"openai/fileParams": ["files"]},
    )
    async def test_mcp_content_transport(
        case: ProbeCaseArg,
        files: ProbeFilesArg = None,
    ) -> list[ProbeContent]:
        if case == "image_content":
            return [
                ImageContent(
                    type="image",
                    data=_TEST_PNG_BASE64,
                    mime_type="image/png",
                    _meta={"probe_case": case, "fixture_bytes": 75},
                )
            ]

        if case == "image_content_with_text":
            return [
                TextContent(type="text", text="probe marker: image_content_with_text"),
                ImageContent(
                    type="image",
                    data=_TEST_PNG_BASE64,
                    mime_type="image/png",
                    _meta={"probe_case": case, "fixture_bytes": 75},
                ),
            ]

        if case == "embedded_text":
            return [
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri="albayan://diagnostics/transport-probe.txt",
                        mime_type="text/plain",
                        text="Al-Bayan MCP embedded text transport probe.",
                    ),
                    _meta={"probe_case": case},
                )
            ]

        if case == "embedded_binary":
            return [
                _embedded_blob(
                    uri="albayan://diagnostics/transport-probe.bin",
                    mime_type="application/octet-stream",
                    blob=base64.b64encode(_TEST_BINARY).decode("ascii"),
                    case=case,
                    size=len(_TEST_BINARY),
                )
            ]

        if case == "embedded_png":
            return [
                _embedded_blob(
                    uri="albayan://diagnostics/transport-probe.png",
                    mime_type="image/png",
                    blob=_TEST_PNG_BASE64,
                    case=case,
                    size=75,
                )
            ]

        if case == "embedded_pdf":
            return [
                _embedded_blob(
                    uri="albayan://diagnostics/transport-probe.pdf",
                    mime_type="application/pdf",
                    blob=_TEST_PDF_BASE64,
                    case=case,
                    size=608,
                )
            ]

        if case == "embedded_pdf_with_text":
            return [
                TextContent(type="text", text="probe marker: embedded_pdf_with_text"),
                _embedded_blob(
                    uri="albayan://diagnostics/transport-probe.pdf",
                    mime_type="application/pdf",
                    blob=_TEST_PDF_BASE64,
                    case=case,
                    size=608,
                ),
            ]

        # case == "upload_file_params"
        return [TextContent(type="text", text=_safe_upload_summary(files))]
