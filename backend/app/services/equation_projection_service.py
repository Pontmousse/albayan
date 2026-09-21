"""Compact read-only projection of Document2 math tokens for AI/MCP consumers."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from app.services import burhan_client, equation_mapping_service

_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
_INLINE_MATH_MODES = {"$", r"\("}


def _math_token_count(sidecar: Any) -> int:
    if not isinstance(sidecar, dict):
        return 0
    tokens = sidecar.get("tokens")
    if not isinstance(tokens, list):
        return 0
    return sum(
        1
        for token in tokens
        if isinstance(token, dict) and token.get("kind") == "math"
    )


def _source_slice(value: str, token: Mapping[str, Any]) -> str:
    start = token.get("start")
    end = token.get("end")
    if (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start <= end <= len(value)
    ):
        return value[start:end]
    return ""


def _field_candidates(
    *,
    block_id: str,
    value: Any,
    inline_ids: Any,
    math_objects: Any,
    container: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, str) or not isinstance(inline_ids, dict):
        return []
    field_id = inline_ids.get("field_id")
    tokens = inline_ids.get("tokens")
    if not isinstance(field_id, str) or not isinstance(tokens, list):
        return []

    objects = math_objects if isinstance(math_objects, list) else []
    math_index = 0
    result: list[dict[str, Any]] = []
    for token in tokens:
        if not isinstance(token, dict) or token.get("kind") != "math":
            continue
        token_id = token.get("id")
        if not isinstance(token_id, str):
            math_index += 1
            continue
        math_object = objects[math_index] if math_index < len(objects) else None
        math_index += 1
        result.append(
            {
                "block_id": block_id,
                "field_id": field_id,
                "token_id": token_id,
                "container": container,
                "source": _source_slice(value, token),
                "math_object": math_object,
            }
        )
    return result


def _iter_blocks(blocks: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(blocks, list):
        return

    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = block.get("id")
        command = block.get("command")
        if not isinstance(block_id, str) or not isinstance(command, str):
            continue

        if command in {r"\section", r"\subsection", r"\subsubsection", r"\paragraph"}:
            container = "paragraph" if command == r"\paragraph" else "heading"
            yield from _field_candidates(
                block_id=block_id,
                value=block.get("value"),
                inline_ids=block.get("inline_ids"),
                math_objects=block.get("math_objects"),
                container=container,
            )
            continue

        if command in {r"\begin{itemize}", r"\begin{enumerate}"}:
            items = block.get("items")
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                yield from _field_candidates(
                    block_id=block_id,
                    value=item.get("value"),
                    inline_ids=item.get("inline_ids"),
                    math_objects=item.get("math_objects"),
                    container="list_item",
                )
                yield from _iter_blocks(item.get("blocks"))
            continue

        if command == r"\begin{tabular}":
            rows = block.get("rows")
            cell_ids = block.get("cell_inline_ids")
            flat_math = block.get("math_objects")
            flat_math = flat_math if isinstance(flat_math, list) else []
            math_cursor = 0
            if isinstance(rows, list) and isinstance(cell_ids, list):
                for row_index, row in enumerate(rows):
                    if not isinstance(row, list):
                        continue
                    id_row = cell_ids[row_index] if row_index < len(cell_ids) else []
                    if not isinstance(id_row, list):
                        id_row = []
                    for column_index, value in enumerate(row):
                        sidecar = id_row[column_index] if column_index < len(id_row) else None
                        count = _math_token_count(sidecar)
                        cell_math = flat_math[math_cursor : math_cursor + count]
                        math_cursor += count
                        yield from _field_candidates(
                            block_id=block_id,
                            value=value,
                            inline_ids=sidecar,
                            math_objects=cell_math,
                            container="table_cell",
                        )
            yield from _field_candidates(
                block_id=block_id,
                value=block.get("caption"),
                inline_ids=block.get("caption_inline_ids"),
                math_objects=block.get("caption_math_objects"),
                container="table_caption",
            )
            continue

        if command == r"\includegraphics":
            yield from _field_candidates(
                block_id=block_id,
                value=block.get("caption"),
                inline_ids=block.get("caption_inline_ids"),
                math_objects=block.get("caption_math_objects"),
                container="figure_caption",
            )


def _math_object_display(math_object: Mapping[str, Any], source: str) -> bool:
    mode = math_object.get("math_mode")
    if isinstance(mode, str):
        return mode not in _INLINE_MATH_MODES
    stripped = source.strip()
    return stripped.startswith(("$$", r"\[", r"\begin{"))


def _raw_display(source: str) -> bool:
    stripped = source.strip()
    return stripped.startswith(("$$", r"\[", r"\begin{"))


def _label(math_object: Mapping[str, Any]) -> str | None:
    if math_object.get("label_enabled") is not True:
        return None
    value = math_object.get("label")
    return value if isinstance(value, str) and value.strip() else None


def _arabic_char_values(value: Any) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("node_type") == "CharObject":
                expr = node.get("expr")
                if isinstance(expr, str) and _ARABIC_RE.search(expr):
                    found.append(expr)
            for child in node.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return found


def _mapping_warnings(
    math_object: Mapping[str, Any],
    reverse_mapping: Mapping[str, str],
    ambiguous_values: set[str],
) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for expr in _arabic_char_values(math_object):
        if expr in ambiguous_values:
            warning = f"ambiguous_reverse_mapping:{expr}"
        elif expr not in reverse_mapping:
            warning = f"unmapped_arabic_variable:{expr}"
        else:
            continue
        if warning not in seen:
            warnings.append(warning)
            seen.add(warning)
    return warnings


def project_document_equations(
    document: Mapping[str, Any],
    variable_mappings: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Return compact, targetable equations without mutating the draft or mappings."""
    reverse_mapping, ambiguous_values = (
        equation_mapping_service.invert_unique_equation_mappings(variable_mappings)
    )
    equations: list[dict[str, Any]] = []

    for candidate in _iter_blocks(document.get("blocks")):
        raw_object = candidate.pop("math_object", None)
        source = candidate.pop("source", "")
        if not isinstance(raw_object, dict) or raw_object.get("node_type") != "MathObject":
            label = _label(raw_object) if isinstance(raw_object, dict) else None
            equations.append(
                {
                    **candidate,
                    "latex": None,
                    "display": _raw_display(source),
                    "label": label,
                    "editable": False,
                    "warnings": ["unstructured_math"],
                }
            )
            continue

        warnings = _mapping_warnings(raw_object, reverse_mapping, ambiguous_values)
        latex, conversion_warnings = burhan_client.convert_math_object_to_english(
            raw_object,
            variable_mapping=reverse_mapping,
        )
        for warning in conversion_warnings:
            if warning not in warnings:
                warnings.append(warning)

        equations.append(
            {
                **candidate,
                "latex": latex,
                "display": _math_object_display(raw_object, source),
                "label": _label(raw_object),
                "editable": True,
                **({"warnings": warnings} if warnings else {}),
            }
        )

    return equations
