"""Display taxonomy for the authoritative Document2 command union."""

from __future__ import annotations


DOCUMENT2_COMMAND_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "block_editing",
        (
            "insert_text_block",
            "replace_text_block",
            "remove_block",
            "move_block",
        ),
    ),
    (
        "figures_floats",
        (
            "insert_figure",
            "update_figure",
            "update_float_meta",
        ),
    ),
    (
        "document_references",
        (
            "insert_bibliography",
            "update_document_meta",
            "insert_reference",
            "update_reference",
            "remove_reference",
            "move_reference",
        ),
    ),
    (
        "inline_tokens",
        (
            "insert_inline_token",
            "replace_inline_token",
            "remove_inline_token",
        ),
    ),
    (
        "lists",
        (
            "insert_list",
            "insert_list_item",
            "replace_list_item",
            "remove_list_item",
            "move_list_item",
        ),
    ),
    (
        "tables",
        (
            "insert_table",
            "replace_table_cell",
            "insert_table_row",
            "remove_table_row",
            "move_table_row",
            "insert_table_column",
            "remove_table_column",
            "move_table_column",
        ),
    ),
)

DOCUMENT2_COMMAND_GROUP_BY_NAME = {
    command_name: group_key
    for group_key, command_names in DOCUMENT2_COMMAND_GROUPS
    for command_name in command_names
}
