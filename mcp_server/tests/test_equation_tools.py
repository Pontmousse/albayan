import inspect
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from mcp.server.mcpserver import MCPServer

from albayan_mcp.tools.equations import register_equation_tools
from tests.test_profile_tools import FakeServer


class EquationToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server = FakeServer()
        register_equation_tools(self.server)
        self.article_id = uuid.uuid4()

    def test_tool_is_read_only_and_accepts_only_article_id(self) -> None:
        self.assertEqual(set(self.server.tools), {"get_draft_equations"})
        self.assertEqual(
            list(inspect.signature(self.server.tools["get_draft_equations"]).parameters),
            ["article_id"],
        )
        description = self.server.tool_options["get_draft_equations"]["description"]
        self.assertIn("Arabic", description)
        self.assertIn("canonical English", description)
        self.assertIn("pure read", description)

    async def test_get_draft_equations_preserves_compact_context_and_targets(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 8,
            "document_language": "ar",
            "equation_representation": "canonical_english_latex",
            "variable_mappings": {"x": "س"},
            "equations": [
                {
                    "block_id": "block-1",
                    "field_id": "field-1",
                    "token_id": "math-1",
                    "container": "paragraph",
                    "latex": "x^2=1",
                    "display": True,
                    "label": "eq:one",
                    "editable": True,
                    "warnings": ["unmapped_arabic_variable:ع"],
                }
            ],
        }
        with patch(
            "albayan_mcp.tools.equations.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_draft_equations"](self.article_id)

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/draft/equations"
        )
        self.assertEqual(result.document_language, "ar")
        self.assertEqual(result.equation_representation, "canonical_english_latex")
        self.assertEqual(result.variable_mappings, {"x": "س"})
        self.assertEqual(result.equations[0].token_id, "math-1")
        self.assertEqual(result.equations[0].latex, "x^2=1")
        self.assertEqual(
            result.equations[0].warnings,
            ["unmapped_arabic_variable:ع"],
        )

    async def test_empty_equation_inventory_is_valid(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 1,
            "document_language": "ar",
            "equation_representation": "canonical_english_latex",
            "variable_mappings": {},
            "equations": [],
        }
        with patch(
            "albayan_mcp.tools.equations.api_get_object",
            new=AsyncMock(return_value=response),
        ):
            result = await self.server.tools["get_draft_equations"](self.article_id)

        self.assertEqual(result.equations, [])

    async def test_real_discovery_has_typed_output_schema(self) -> None:
        server = MCPServer("equation-schema-test")
        register_equation_tools(server)
        published = {tool.name: tool for tool in await server.list_tools()}

        self.assertEqual(set(published), {"get_draft_equations"})
        tool = published["get_draft_equations"]
        self.assertEqual(set(tool.input_schema["properties"]), {"article_id"})
        self.assertIsNotNone(tool.output_schema)
        self.assertIn("variable_mappings", tool.output_schema["properties"])
        self.assertIn("equations", tool.output_schema["properties"])


if __name__ == "__main__":
    unittest.main()
