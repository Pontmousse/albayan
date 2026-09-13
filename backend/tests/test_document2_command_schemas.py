from __future__ import annotations

import unittest
import uuid

from pydantic import ValidationError

from app.schemas.article import DocumentCommandPayload


def _math_object() -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [{"node_type": "NumberObject", "expr": "1"}],
            }
        ],
        "closing": "$",
        "source_side": "english",
        "source_owner": "editor",
    }


VALID_COMMANDS = [
    {
        "op": "insert_text_block",
        "kind": "paragraph",
        "text": "نص",
        "anchor": {"before_block_id": "block_2"},
        "metadata": {"source": "agent"},
    },
    {"op": "replace_text_block", "block_id": "block_1", "text": "بديل"},
    {"op": "remove_block", "block_id": "block_1"},
    {
        "op": "move_block",
        "block_id": "block_1",
        "anchor": {"after_block_id": "block_2"},
    },
    {
        "op": "insert_figure",
        "asset_id": "figures/a.png",
        "value": "figures/a.png",
        "caption": "شكل",
        "label": "fig:a",
        "anchor": {"end": True},
        "metadata": {"source": "user"},
    },
    {
        "op": "update_figure",
        "block_id": "figure_1",
        "asset_id": None,
        "value": "",
    },
    {
        "op": "update_float_meta",
        "block_id": "figure_1",
        "centered": False,
        "caption_enabled": True,
        "caption": "شكل",
        "label_enabled": True,
        "label": "fig:a",
    },
    {
        "op": "insert_bibliography",
        "anchor": {"end": True},
        "metadata": {"source": "agent"},
    },
    {
        "op": "update_document_meta",
        "title": "عنوان",
        "authors": "مؤلف",
        "abstract": "ملخص",
        "date": {"day": 1, "month": "محرم", "year": 1448},
    },
    {
        "op": "insert_reference",
        "key": "ref:a",
        "authors": "مؤلف",
        "title": "كتاب",
        "year": "1448",
        "venue": "مجلة",
        "url": "https://example.com",
        "field_separator": "،",
        "anchor": {"end": True},
    },
    {
        "op": "update_reference",
        "reference_key": "ref:a",
        "key": "ref:b",
        "title": "عنوان جديد",
        "field_separator": ",",
    },
    {"op": "remove_reference", "reference_key": "ref:a"},
    {
        "op": "move_reference",
        "reference_key": "ref:a",
        "anchor": {"before_reference_key": "ref:b"},
    },
    {
        "op": "insert_inline_token",
        "field_id": "field_1",
        "token": {
            "kind": "text",
            "text": "نص",
            "style": {"bold": True, "italic": True, "underline": True},
        },
        "anchor": {"start": True},
    },
    {
        "op": "replace_inline_token",
        "field_id": "field_1",
        "token_id": "token_1",
        "token": {"kind": "math", "source": "$1$", "math_object": _math_object()},
    },
    {
        "op": "remove_inline_token",
        "field_id": "field_1",
        "token_id": "token_1",
    },
    {
        "op": "insert_list",
        "ordered": True,
        "items": ["الأول", "الثاني"],
        "anchor": {"end": True},
        "metadata": {"source": "agent"},
    },
    {
        "op": "insert_list_item",
        "list_id": "list_1",
        "text": "عنصر",
        "anchor": {"after_item_id": "item_1"},
    },
    {
        "op": "replace_list_item",
        "list_id": "list_1",
        "item_id": "item_1",
        "text": "بديل",
    },
    {"op": "remove_list_item", "list_id": "list_1", "item_id": "item_1"},
    {
        "op": "move_list_item",
        "list_id": "list_1",
        "item_id": "item_1",
        "anchor": {"before_item_id": "item_2"},
    },
    {
        "op": "insert_table",
        "rows": [["a", "b"], ["c", "d"]],
        "columns": "cc",
        "caption": "جدول",
        "label": "tab:a",
        "anchor": {"end": True},
        "metadata": {"source": "user"},
    },
    {
        "op": "replace_table_cell",
        "table_id": "table_1",
        "row_index": 0,
        "column_index": 1,
        "text": "x",
    },
    {
        "op": "insert_table_row",
        "table_id": "table_1",
        "index": 1,
        "values": ["a", "b"],
    },
    {"op": "remove_table_row", "table_id": "table_1", "index": 0},
    {
        "op": "move_table_row",
        "table_id": "table_1",
        "from_index": 0,
        "to_index": 1,
    },
    {
        "op": "insert_table_column",
        "table_id": "table_1",
        "index": 1,
        "values": ["a", "b"],
        "columns": "ccc",
    },
    {
        "op": "remove_table_column",
        "table_id": "table_1",
        "index": 1,
        "columns": "c",
    },
    {
        "op": "move_table_column",
        "table_id": "table_1",
        "from_index": 0,
        "to_index": 1,
        "columns": "cc",
    },
]


class Document2CommandSchemaTests(unittest.TestCase):
    def _payload(self, command: dict) -> DocumentCommandPayload:
        return DocumentCommandPayload(
            command_id=uuid.uuid4(),
            base_revision=0,
            command=command,
        )

    def test_all_29_published_commands_round_trip_without_coercion(self) -> None:
        self.assertEqual(len(VALID_COMMANDS), 29)
        for command in VALID_COMMANDS:
            with self.subTest(op=command["op"]):
                parsed = self._payload(command)
                self.assertEqual(
                    parsed.command.model_dump(exclude_unset=True),
                    command,
                )

    def test_rejects_invalid_command_shapes(self) -> None:
        invalid_commands = [
            {
                "op": "insert_text_block",
                "kind": "paragraph",
                "text": "x",
                "anchor": {},
            },
            {
                "op": "insert_text_block",
                "kind": "paragraph",
                "text": "x",
                "anchor": {"after_block_id": "a", "end": True},
            },
            {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "token": {"kind": "text", "text": "x"},
                "anchor": {"start": True, "end": True},
            },
            {
                "op": "insert_list_item",
                "list_id": "list_1",
                "text": "x",
                "anchor": {},
            },
            {
                "op": "move_reference",
                "reference_key": "ref:a",
                "anchor": {"before_reference_key": "ref:b", "end": True},
            },
            {"op": "remove_block", "block_id": "b", "unknown": True},
            {"op": "unknown"},
            {
                "op": "remove_block",
                "block_id": "b",
                "host_extra": "not-allowed",
            },
            {
                "op": "insert_list",
                "ordered": 1,
                "items": ["x"],
                "anchor": {"end": True},
            },
            {"op": "update_figure", "block_id": "figure_1"},
            {"op": "update_float_meta", "block_id": "figure_1"},
            {"op": "update_document_meta"},
            {"op": "update_document_meta", "date": {}},
            {"op": "update_document_meta", "date": {"year": 1501}},
            {"op": "update_reference", "reference_key": "ref:a"},
            {
                "op": "insert_table",
                "rows": [["a"], ["b", "c"]],
                "columns": "cc",
                "anchor": {"end": True},
            },
            {
                "op": "replace_table_cell",
                "table_id": "table_1",
                "row_index": "0",
                "column_index": 0,
                "text": "x",
            },
            {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "token": {"kind": "text", "text": "x", "style": {"bold": False}},
                "anchor": {"end": True},
            },
            {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "token": {"kind": "cite", "keys": [" "]},
                "anchor": {"end": True},
            },
            {
                "op": "insert_inline_token",
                "field_id": "field_1",
                "token": {
                    "kind": "math",
                    "source": "$1$",
                    "math_object": {
                        "node_type": "MathObject",
                        "math_mode": "$",
                        "closing": "$",
                    },
                },
                "anchor": {"end": True},
            },
            {
                "op": "insert_figure",
                "asset_id": "a.png",
                "caption": None,
                "anchor": {"end": True},
            },
        ]

        for command in invalid_commands:
            with self.subTest(command=command), self.assertRaises(ValidationError):
                self._payload(command)

    def test_update_figure_explicit_null_is_preserved(self) -> None:
        command = {
            "op": "update_figure",
            "block_id": "figure_1",
            "asset_id": None,
        }
        parsed = self._payload(command)

        self.assertEqual(parsed.command.model_dump(exclude_unset=True), command)

    def test_host_envelope_rejects_unknown_fields_and_revision_coercion(self) -> None:
        command = {"op": "remove_block", "block_id": "block_1"}
        with self.assertRaises(ValidationError):
            DocumentCommandPayload(
                command_id=uuid.uuid4(),
                base_revision="0",
                command=command,
            )
        with self.assertRaises(ValidationError):
            DocumentCommandPayload(
                command_id=uuid.uuid4(),
                base_revision=0,
                command=command,
                article_id="host-only-extra",
            )


if __name__ == "__main__":
    unittest.main()
