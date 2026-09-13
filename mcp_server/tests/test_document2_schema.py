from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from typing import get_type_hints

from mcp.server.mcpserver import MCPServer
from pydantic import TypeAdapter

from albayan_mcp.schemas.document2 import DocumentCommand
from albayan_mcp.tools.sessions import register_session_tools
from tests.test_profile_tools import FakeServer


EXPECTED_OPERATIONS = {
    "insert_text_block",
    "replace_text_block",
    "remove_block",
    "move_block",
    "insert_figure",
    "update_figure",
    "update_float_meta",
    "insert_bibliography",
    "update_document_meta",
    "insert_reference",
    "update_reference",
    "remove_reference",
    "move_reference",
    "insert_inline_token",
    "replace_inline_token",
    "remove_inline_token",
    "insert_list",
    "insert_list_item",
    "replace_list_item",
    "remove_list_item",
    "move_list_item",
    "insert_table",
    "replace_table_cell",
    "insert_table_row",
    "remove_table_row",
    "move_table_row",
    "insert_table_column",
    "remove_table_column",
    "move_table_column",
}


def _without_documentation(value):
    if isinstance(value, dict):
        return {
            key: _without_documentation(item)
            for key, item in value.items()
            if key not in {"title", "description"}
        }
    if isinstance(value, list):
        return [_without_documentation(item) for item in value]
    return value


class Document2McpSchemaTests(unittest.TestCase):
    def test_command_schema_is_discriminated_and_has_all_29_variants(self) -> None:
        schema = TypeAdapter(DocumentCommand).json_schema()

        self.assertEqual(schema["discriminator"]["propertyName"], "op")
        self.assertEqual(set(schema["discriminator"]["mapping"]), EXPECTED_OPERATIONS)
        self.assertEqual(len(schema["oneOf"]), 29)
        self.assertTrue(all("$ref" in variant for variant in schema["oneOf"]))

    def test_apply_tool_signature_publishes_typed_command_union(self) -> None:
        server = FakeServer()
        register_session_tools(server)
        tool = server.tools["apply_session_command"]
        signature = inspect.signature(tool)
        hints = get_type_hints(tool, include_extras=True)

        self.assertEqual(list(signature.parameters), [
            "article_id", "command_id", "base_revision", "command"
        ])
        command_schema = TypeAdapter(hints["command"]).json_schema()
        self.assertEqual(command_schema["discriminator"]["propertyName"], "op")
        self.assertEqual(len(command_schema["oneOf"]), 29)

    def test_real_mcp_discovery_publishes_typed_input_and_output_schemas(self) -> None:
        import asyncio

        server = MCPServer("schema-test")
        register_session_tools(server)
        published = {
            tool.name: tool for tool in asyncio.run(server.list_tools())
        }

        self.assertEqual(
            set(published),
            {
                "get_session_outline",
                "get_session_blocks",
                "apply_session_command",
                "save_session",
            },
        )
        edit_schema = published["apply_session_command"].input_schema
        command_schema = edit_schema["properties"]["command"]
        self.assertEqual(command_schema["discriminator"]["propertyName"], "op")
        self.assertEqual(len(command_schema["oneOf"]), 29)
        blocks_schema = published["get_session_blocks"].output_schema
        self.assertIn("DocumentInlineTokenIdentityResult", blocks_schema["$defs"])
        for tool in published.values():
            self.assertIsNotNone(tool.output_schema)

    def test_mcp_schema_matches_backend_authoritative_schema(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        backend_path = str(repository / "backend")
        sys.path.insert(0, backend_path)
        try:
            from app.schemas.document2 import DocumentCommand as BackendDocumentCommand

            backend_schema = TypeAdapter(BackendDocumentCommand).json_schema()
        finally:
            sys.path.remove(backend_path)

        mcp_schema = TypeAdapter(DocumentCommand).json_schema()
        self.assertEqual(
            _without_documentation(mcp_schema),
            _without_documentation(backend_schema),
        )

    def test_mcp_source_has_no_private_worker_or_storage_coupling(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src" / "albayan_mcp"
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in source_root.rglob("*.py")
        ).lower()

        for forbidden in (
            "/v1/document2/",
            "butex_worker_token",
            "butex_worker_url",
            "sqlalchemy",
            "boto3",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
