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

    def test_tools_are_read_only_with_expected_inputs(self) -> None:
        self.assertEqual(
            set(self.server.tools),
            {"get_math_authoring_capabilities", "get_draft_equations"},
        )
        self.assertEqual(
            list(
                inspect.signature(
                    self.server.tools["get_math_authoring_capabilities"]
                ).parameters
            ),
            [],
        )
        self.assertEqual(
            list(inspect.signature(self.server.tools["get_draft_equations"]).parameters),
            ["article_id"],
        )

        capability_description = self.server.tool_options[
            "get_math_authoring_capabilities"
        ]["description"]
        self.assertIn("before generating", capability_description)
        self.assertIn("round_trip_safe", capability_description)
        self.assertIn("Never emit", capability_description)
        self.assertIn("pure-read", capability_description)

        equation_description = self.server.tool_options["get_draft_equations"]["description"]
        self.assertIn("Arabic", equation_description)
        self.assertIn("canonical English", equation_description)
        self.assertIn("pure read", equation_description)

    async def test_get_math_authoring_capabilities_returns_canonical_contract(self) -> None:
        response = {
            "contract_version": 1,
            "canonical_input": True,
            "representation": "canonical_english_latex",
            "instruction": "Use only round_trip_safe.",
            "preferred_submission": {"latex": "body only"},
            "source_snapshot": {
                "burhan": {"commit": "burhan-sha"},
                "butex": {"commit": "butex-sha"},
            },
            "round_trip_safe": {
                "commands": {"structures": [{"command": "\\frac"}]}
            },
            "accepted_but_not_round_trip_safe": {"commands": ["\\partial"]},
            "unsupported_or_forbidden": {
                "internal_output_macro_examples": ["\\arsum"]
            },
            "normalization_aliases": [],
            "constraints": ["Use exact arity."],
            "examples": [{"latex": "\\frac{x}{y}", "display": False}],
        }
        with patch(
            "albayan_mcp.tools.equations.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_math_authoring_capabilities"]()

        get.assert_awaited_once_with("/api/v1/math/authoring-capabilities")
        self.assertTrue(result.canonical_input)
        self.assertEqual(result.representation, "canonical_english_latex")
        self.assertIn("commands", result.round_trip_safe)
        self.assertEqual(
            result.unsupported_or_forbidden["internal_output_macro_examples"],
            ["\\arsum"],
        )

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

    async def test_real_discovery_has_typed_output_schemas(self) -> None:
        server = MCPServer("equation-schema-test")
        register_equation_tools(server)
        published = {tool.name: tool for tool in await server.list_tools()}

        self.assertEqual(
            set(published),
            {"get_math_authoring_capabilities", "get_draft_equations"},
        )

        capability = published["get_math_authoring_capabilities"]
        self.assertEqual(capability.input_schema["properties"], {})
        self.assertIsNotNone(capability.output_schema)
        self.assertIn("round_trip_safe", capability.output_schema["properties"])
        self.assertIn("source_snapshot", capability.output_schema["properties"])

        equations = published["get_draft_equations"]
        self.assertEqual(set(equations.input_schema["properties"]), {"article_id"})
        self.assertIsNotNone(equations.output_schema)
        self.assertIn("variable_mappings", equations.output_schema["properties"])
        self.assertIn("equations", equations.output_schema["properties"])


if __name__ == "__main__":
    unittest.main()
