"""Normal MCP unit-conventions contract: real tool discovery and FastAPI forwarding."""

from __future__ import annotations

import unittest
import uuid
from unittest.mock import AsyncMock, patch

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from albayan_mcp.tools.units import UnitConventionsInput, register_unit_tools
from tests.test_profile_tools import FakeServer


ARTICLE = uuid.UUID("1c7d9877-9a78-40a1-9b80-37d85ba2f42e")
REGISTRY = {
    "version": 1,
    "canonical_syntax": r"\mathsf{token}",
    "token_pattern": "^[A-Za-z][A-Za-z0-9]*$",
    "notation_only": True,
    "units": {
        "kg": {
            "name_en": "kilogram", "name_ar": "كيلوغرام",
            "default_display": "كلغ", "alternatives": ["كغ"],
        },
        "ha": {
            "name_en": "hectare", "default_display": "هكتار",
            "alternatives": [],
        },
    },
}
CONVENTIONS = {
    "overrides": {"kg": "كغ"},
    "custom_units": {"CU": {"display": "وحدة معايرة", "name": "Calibration unit"}},
}
CONTEXT = {
    "revision_number": 4,
    "unit_conventions": CONVENTIONS,
    "registered_tokens": ["kg", "ha"],
    "used_units": [
        {
            "token": "kg", "usage_count": 3, "status": "registry",
            "display": "كغ", "source": "article_override",
            "name": "kilogram", "name_ar": "كيلوغرام",
            "default_display": "كلغ", "alternatives": ["كغ"],
        },
        {
            "token": "CU", "usage_count": 1, "status": "custom",
            "display": "وحدة معايرة", "source": "article_custom",
        },
        {
            "token": "XYZ", "usage_count": 1, "status": "unknown",
            "display": "XYZ", "source": "unknown",
        },
    ],
}


class NormalMcpUnitsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = FakeServer()
        register_unit_tools(self.server)

    def test_discovery_includes_scoped_tools_and_explicit_rules(self):
        self.assertEqual(
            set(self.server.tools),
            {"get_unit_registry", "get_article_unit_context", "apply_article_unit_conventions"},
        )
        descriptions = self.server.tool_options
        self.assertIn("canonical", descriptions["get_unit_registry"]["description"])
        self.assertIn(r"\mathsf{token}", descriptions["get_unit_registry"]["description"])
        self.assertIn("Unknown explicit", descriptions["get_unit_registry"]["description"])
        self.assertIn("No numerical conversion", descriptions["get_unit_registry"]["description"])
        self.assertIn("variable_mappings", descriptions["get_article_unit_context"]["description"])
        self.assertIn("immutable", descriptions["apply_article_unit_conventions"]["description"])

    async def test_global_registry_comes_from_fastapi_not_local_copy(self):
        with patch(
            "albayan_mcp.tools.units.api_get_object",
            new=AsyncMock(return_value=REGISTRY),
        ) as get:
            result = await self.server.tools["get_unit_registry"]()
        get.assert_awaited_once_with("/api/v1/math/unit-registry")
        self.assertEqual(result.units["kg"]["alternatives"], ["كغ"])
        self.assertEqual(result.units["ha"]["default_display"], "هكتار")
        self.assertTrue(result.notation_only)

    async def test_article_state_includes_custom_known_and_unknown_identity(self):
        with patch(
            "albayan_mcp.tools.units.api_get_object",
            new=AsyncMock(return_value=CONTEXT),
        ) as get:
            result = await self.server.tools["get_article_unit_context"](ARTICLE)
        get.assert_awaited_once_with(
            f"/api/v1/articles/{ARTICLE}/unit-conventions/used"
        )
        self.assertEqual(result.unit_conventions.overrides["kg"], "كغ")
        self.assertEqual(result.unit_conventions.custom_units["CU"].display, "وحدة معايرة")
        self.assertEqual(
            {(u.token, u.status) for u in result.used_units},
            {("kg", "registry"), ("CU", "custom"), ("XYZ", "unknown")},
        )
        self.assertEqual(result.revision_number, 4)

    async def test_apply_uses_full_typed_payload_and_draft_revision(self):
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 5, "document_hash": "a" * 64,
            "actor_type": "agent", "reason": "unit_conventions",
            "unit_conventions": CONVENTIONS, "document": {"blocks": []},
            "affected_block_ids": ["block-1"],
            "used_units": CONTEXT["used_units"],
        }
        with patch(
            "albayan_mcp.tools.units.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            result = await self.server.tools["apply_article_unit_conventions"](
                ARTICLE, 4, UnitConventionsInput.model_validate(CONVENTIONS)
            )
        post.assert_awaited_once_with(
            f"/api/v1/articles/{ARTICLE}/unit-conventions/apply",
            json={"base_revision": 4, "unit_conventions": CONVENTIONS},
        )
        self.assertEqual(result.revision_number, 5)
        self.assertEqual(result.reason, "unit_conventions")
        self.assertEqual(result.affected_block_ids, ["block-1"])

    def test_invalid_extra_convention_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            UnitConventionsInput.model_validate({
                "overrides": {}, "custom_units": {},
                "variable_mappings": {"N": "ن"},
            })

    async def test_real_mcp_tool_schemas_are_machine_discoverable(self):
        server = MCPServer("units-contract-test")
        register_unit_tools(server)
        published = {item.name: item for item in await server.list_tools()}
        self.assertEqual(
            set(published),
            {"get_unit_registry", "get_article_unit_context", "apply_article_unit_conventions"},
        )
        self.assertEqual(published["get_unit_registry"].input_schema["properties"], {})
        self.assertEqual(
            set(published["get_article_unit_context"].input_schema["properties"]),
            {"article_id"},
        )
        self.assertEqual(
            set(published["apply_article_unit_conventions"].input_schema["properties"]),
            {"article_id", "base_revision", "unit_conventions"},
        )
        registry_schema = published["get_unit_registry"].output_schema
        self.assertIn("units", registry_schema["properties"])
        context_schema = published["get_article_unit_context"].output_schema
        self.assertIn("unit_conventions", context_schema["properties"])
        self.assertIn("used_units", context_schema["properties"])

    async def test_real_mcp_transport_preserves_unit_result(self):
        server = MCPServer("units-call-test")
        register_unit_tools(server)
        with patch(
            "albayan_mcp.tools.units.api_get_object",
            new=AsyncMock(return_value=CONTEXT),
        ):
            call = await server.call_tool(
                "get_article_unit_context", {"article_id": str(ARTICLE)}
            )
        self.assertFalse(call.is_error)
        self.assertEqual(
            call.structured_content["unit_conventions"]["custom_units"]["CU"]["display"],
            "وحدة معايرة",
        )


if __name__ == "__main__":
    unittest.main()
