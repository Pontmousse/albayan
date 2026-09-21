import uuid

import pytest
from pydantic import TypeAdapter

from albayan_mcp.schemas.draft_command import DocumentCommand


adapter = TypeAdapter(DocumentCommand)


def test_mcp_schema_accepts_compact_math_insert() -> None:
    command = adapter.validate_python(
        {
            "op": "insert_inline_token",
            "field_id": "field_1",
            "anchor": {"end": True},
            "token": {
                "kind": "math",
                "latex": r"E=mc^2",
                "display": False,
            },
        }
    )

    assert command.token.kind == "math"
    assert command.token.latex == r"E=mc^2"


def test_mcp_schema_keeps_existing_remove_math_path() -> None:
    command = adapter.validate_python(
        {
            "op": "remove_inline_token",
            "field_id": "field_1",
            "token_id": "math_1",
        }
    )

    assert command.op == "remove_inline_token"
    assert command.token_id == "math_1"


def test_mcp_schema_rejects_inline_equation_label() -> None:
    with pytest.raises(ValueError):
        adapter.validate_python(
            {
                "op": "replace_inline_token",
                "field_id": "field_1",
                "token_id": "math_1",
                "token": {
                    "kind": "math",
                    "latex": "x=1",
                    "display": False,
                    "label": f"eq:{uuid.uuid4()}",
                },
            }
        )
