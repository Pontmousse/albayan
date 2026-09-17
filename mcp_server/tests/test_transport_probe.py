from __future__ import annotations

import asyncio
import base64
import json
import unittest

from mcp.server.mcpserver import MCPServer
from mcp.types import EmbeddedResource, ImageContent, TextContent

from albayan_mcp.tools.transport_probe import register_transport_probe_tool
from tests.test_profile_tools import FakeServer


class TransportProbeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server = FakeServer()
        register_transport_probe_tool(self.server)

    def test_registration_exposes_one_diagnostic_tool(self) -> None:
        self.assertEqual(set(self.server.tools), {"test_mcp_content_transport"})
        options = self.server.tool_options["test_mcp_content_transport"]
        self.assertEqual(options["meta"], {"openai/fileParams": ["files"]})
        self.assertTrue(options["annotations"].read_only_hint)
        self.assertFalse(options["annotations"].destructive_hint)

    async def test_image_content_fixture_is_real_png(self) -> None:
        result = await self.server.tools["test_mcp_content_transport"]("image_content")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ImageContent)
        self.assertEqual(result[0].mime_type, "image/png")
        body = base64.b64decode(result[0].data)
        self.assertEqual(len(body), 75)
        self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))

    async def test_embedded_pdf_fixture_is_real_pdf(self) -> None:
        result = await self.server.tools["test_mcp_content_transport"]("embedded_pdf")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], EmbeddedResource)
        resource = result[0].resource
        self.assertEqual(resource.mime_type, "application/pdf")
        body = base64.b64decode(resource.blob)
        self.assertEqual(len(body), 608)
        self.assertTrue(body.startswith(b"%PDF-1.4"))
        self.assertTrue(body.rstrip().endswith(b"%%EOF"))

    async def test_embedded_text_and_generic_binary_are_distinct(self) -> None:
        text_result = await self.server.tools["test_mcp_content_transport"]("embedded_text")
        binary_result = await self.server.tools["test_mcp_content_transport"]("embedded_binary")
        self.assertEqual(text_result[0].resource.mime_type, "text/plain")
        self.assertEqual(binary_result[0].resource.mime_type, "application/octet-stream")
        self.assertEqual(
            base64.b64decode(binary_result[0].resource.blob),
            b"\x00\x01Al-Bayan-MCP\xfe\xff",
        )

    async def test_with_text_cases_keep_both_content_blocks(self) -> None:
        image_result = await self.server.tools["test_mcp_content_transport"](
            "image_content_with_text"
        )
        pdf_result = await self.server.tools["test_mcp_content_transport"](
            "embedded_pdf_with_text"
        )
        self.assertIsInstance(image_result[0], TextContent)
        self.assertIsInstance(image_result[1], ImageContent)
        self.assertIsInstance(pdf_result[0], TextContent)
        self.assertIsInstance(pdf_result[1], EmbeddedResource)

    async def test_upload_probe_sanitizes_web_file_object(self) -> None:
        result = await self.server.tools["test_mcp_content_transport"](
            "upload_file_params",
            [
                {
                    "download_url": "https://files.oaiusercontent.com/secret-signed-value",
                    "file_id": "file-secret-id",
                    "mime_type": "image/png",
                    "file_name": "probe.png",
                    "size": 123,
                }
            ],
        )
        payload = json.loads(result[0].text)
        self.assertEqual(payload["received_count"], 1)
        self.assertEqual(payload["items"][0]["kind"], "object")
        self.assertTrue(payload["items"][0]["has_download_url"])
        self.assertTrue(payload["items"][0]["has_file_id"])
        self.assertEqual(payload["items"][0]["download_url_scheme"], "https")
        self.assertNotIn("secret-signed-value", result[0].text)
        self.assertNotIn("file-secret-id", result[0].text)

    async def test_upload_probe_accepts_reported_mobile_string_reference(self) -> None:
        result = await self.server.tools["test_mcp_content_transport"](
            "upload_file_params",
            ["chat_upload://image_0"],
        )
        payload = json.loads(result[0].text)
        self.assertEqual(payload["received_count"], 1)
        self.assertEqual(payload["items"][0]["kind"], "string")
        self.assertTrue(payload["items"][0]["chat_upload_reference"])
        self.assertEqual(payload["items"][0]["scheme"], "chat_upload")

    async def test_real_mcp_call_preserves_native_content_blocks(self) -> None:
        server = MCPServer("transport-probe-call-test")
        register_transport_probe_tool(server)

        image = await server.call_tool(
            "test_mcp_content_transport", {"case": "image_content"}
        )
        pdf = await server.call_tool(
            "test_mcp_content_transport", {"case": "embedded_pdf"}
        )

        self.assertFalse(image.is_error)
        self.assertFalse(pdf.is_error)
        self.assertIsInstance(image.content[0], ImageContent)
        self.assertIsInstance(pdf.content[0], EmbeddedResource)
        self.assertIsNone(image.structured_content)
        self.assertIsNone(pdf.structured_content)

    def test_real_discovery_exposes_case_and_file_params_without_output_schema(self) -> None:
        server = MCPServer("transport-probe-schema-test")
        register_transport_probe_tool(server)
        published = {tool.name: tool for tool in asyncio.run(server.list_tools())}
        tool = published["test_mcp_content_transport"]

        self.assertEqual(tool.meta["openai/fileParams"], ["files"])
        self.assertEqual(set(tool.input_schema["properties"]), {"case", "files"})
        case_schema = tool.input_schema["properties"]["case"]
        self.assertIn("image_content", case_schema["enum"])
        self.assertIn("embedded_pdf", case_schema["enum"])
        self.assertIn("upload_file_params", case_schema["enum"])
        self.assertIsNone(tool.output_schema)


if __name__ == "__main__":
    unittest.main()
