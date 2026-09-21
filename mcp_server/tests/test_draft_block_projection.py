from __future__ import annotations

import unittest
import uuid
from unittest.mock import AsyncMock, patch

from albayan_mcp.tools.block_projection import project_draft_blocks_response
from albayan_mcp.tools.drafts import register_draft_tools
from tests.test_profile_tools import FakeServer

_FORBIDDEN = {"math_objects", "caption_math_objects"}


def _assert_no_structured_math(value) -> None:
    if isinstance(value, dict):
        assert _FORBIDDEN.isdisjoint(value)
        for child in value.values():
            _assert_no_structured_math(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_structured_math(child)


def _math_object(expr: str) -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {
                        "node_type": "CharObject",
                        "expr": expr,
                        "superscript": None,
                        "subscript": None,
                    }
                ],
            }
        ],
    }


class DraftBlockProjectionTests(unittest.IsolatedAsyncioTestCase):
    def test_projection_strips_math_sidecars_recursively_but_keeps_targets(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 12,
            "blocks": [
                {
                    "id": "paragraph-1",
                    "command": r"\paragraph",
                    "value": "قبل $س$ وبعد $ص$",
                    "inline_ids": {
                        "field_id": "field-paragraph",
                        "tokens": [
                            {"id": "text-1", "kind": "text", "start": 0, "end": 4},
                            {"id": "math-1", "kind": "math", "start": 4, "end": 7},
                            {"id": "text-2", "kind": "text", "start": 7, "end": 13},
                            {"id": "math-2", "kind": "math", "start": 13, "end": 16},
                        ],
                    },
                    "math_objects": [_math_object("س"), _math_object("ص")],
                },
                {
                    "id": "list-1",
                    "command": r"\begin{itemize}",
                    "closing": r"\end{itemize}",
                    "items": [
                        {
                            "id": "item-1",
                            "value": "$ع$",
                            "inline_ids": {
                                "field_id": "field-item",
                                "tokens": [
                                    {"id": "math-item", "kind": "math", "start": 0, "end": 3}
                                ],
                            },
                            "math_objects": [_math_object("ع")],
                            "blocks": [
                                {
                                    "id": "nested-1",
                                    "command": r"\paragraph",
                                    "value": "$ل$",
                                    "inline_ids": {
                                        "field_id": "field-nested",
                                        "tokens": [
                                            {"id": "math-nested", "kind": "math", "start": 0, "end": 3}
                                        ],
                                    },
                                    "math_objects": [_math_object("ل")],
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": "table-1",
                    "command": r"\begin{tabular}",
                    "closing": r"\end{tabular}",
                    "columns": "cc",
                    "rows": [["$أ$", "نص"], ["$ب$", "$ج$"]],
                    "cell_inline_ids": [
                        [
                            {
                                "field_id": "cell-a",
                                "tokens": [{"id": "math-a", "kind": "math", "start": 0, "end": 3}],
                            },
                            {"field_id": "cell-text", "tokens": []},
                        ],
                        [
                            {
                                "field_id": "cell-b",
                                "tokens": [{"id": "math-b", "kind": "math", "start": 0, "end": 3}],
                            },
                            {
                                "field_id": "cell-c",
                                "tokens": [{"id": "math-c", "kind": "math", "start": 0, "end": 3}],
                            },
                        ],
                    ],
                    "math_objects": [_math_object("أ"), _math_object("ب"), _math_object("ج")],
                    "caption": "جدول $د$",
                    "caption_inline_ids": {
                        "field_id": "table-caption",
                        "tokens": [{"id": "math-table-caption", "kind": "math", "start": 5, "end": 8}],
                    },
                    "caption_math_objects": [_math_object("د")],
                    "caption_enabled": True,
                    "label_enabled": True,
                    "label": "tab:data",
                },
                {
                    "id": "figure-1",
                    "command": r"\includegraphics",
                    "value": "figure.png",
                    "asset_id": "figure.png",
                    "caption": "شكل $هـ$",
                    "caption_inline_ids": {
                        "field_id": "figure-caption",
                        "tokens": [{"id": "math-figure-caption", "kind": "math", "start": 5, "end": 9}],
                    },
                    "caption_math_objects": [_math_object("هـ")],
                    "caption_enabled": True,
                },
            ],
        }

        projected = project_draft_blocks_response(response)

        self.assertEqual(projected["revision_id"], response["revision_id"])
        self.assertEqual(projected["revision_number"], 12)
        _assert_no_structured_math(projected)

        paragraph = projected["blocks"][0]
        self.assertEqual(paragraph["value"], "قبل $س$ وبعد $ص$")
        self.assertEqual(paragraph["inline_ids"]["field_id"], "field-paragraph")
        self.assertEqual(
            [token["id"] for token in paragraph["inline_ids"]["tokens"] if token["kind"] == "math"],
            ["math-1", "math-2"],
        )

        item = projected["blocks"][1]["items"][0]
        self.assertEqual(item["inline_ids"]["field_id"], "field-item")
        self.assertEqual(item["blocks"][0]["inline_ids"]["field_id"], "field-nested")

        table = projected["blocks"][2]
        self.assertEqual(table["rows"], [["$أ$", "نص"], ["$ب$", "$ج$"]])
        self.assertEqual(table["cell_inline_ids"][1][1]["tokens"][0]["id"], "math-c")
        self.assertEqual(table["caption_inline_ids"]["field_id"], "table-caption")
        self.assertEqual(table["label"], "tab:data")

        figure = projected["blocks"][3]
        self.assertEqual(figure["asset_id"], "figure.png")
        self.assertEqual(figure["caption_inline_ids"]["field_id"], "figure-caption")

        # Projection must not mutate the canonical FastAPI payload.
        self.assertIn("math_objects", response["blocks"][0])
        self.assertIn("caption_math_objects", response["blocks"][2])

    def test_ordinary_non_math_blocks_are_unchanged(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 3,
            "blocks": [
                {
                    "id": "section-1",
                    "command": r"\section",
                    "value": "مقدمة",
                    "inline_ids": {
                        "field_id": "field-section",
                        "tokens": [{"id": "text-1", "kind": "text", "start": 0, "end": 5}],
                    },
                    "formats": [{"start": 0, "end": 5, "bold": True}],
                    "metadata": {"custom": "kept"},
                }
            ],
        }

        self.assertEqual(project_draft_blocks_response(response), response)

    async def test_mcp_get_draft_blocks_projects_backend_response(self) -> None:
        server = FakeServer()
        register_draft_tools(server)
        article_id = uuid.uuid4()
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 5,
            "blocks": [
                {
                    "id": "paragraph-1",
                    "command": r"\paragraph",
                    "value": "$س$",
                    "inline_ids": {
                        "field_id": "field-1",
                        "tokens": [{"id": "math-1", "kind": "math", "start": 0, "end": 3}],
                    },
                    "math_objects": [_math_object("س")],
                }
            ],
        }

        with patch(
            "albayan_mcp.tools.drafts.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await server.tools["get_draft_blocks"](article_id)

        get.assert_awaited_once_with(f"/api/v1/articles/{article_id}/draft/blocks")
        self.assertEqual(result.revision_number, 5)
        self.assertEqual(result.blocks[0]["inline_ids"]["field_id"], "field-1")
        self.assertEqual(result.blocks[0]["inline_ids"]["tokens"][0]["id"], "math-1")
        self.assertNotIn("math_objects", result.blocks[0])
        description = server.tool_options["get_draft_blocks"]["description"]
        self.assertIn("get_draft_equations", description)
        self.assertIn("omitted", description)


if __name__ == "__main__":
    unittest.main()
