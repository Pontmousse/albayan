import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app.services import (
    burhan_reverse_client,
    draft_equation_service,
    equation_projection_service,
)


def _math(
    expr: str,
    *,
    mode: str = "$",
    closing: str = "$",
    label: str | None = None,
) -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": mode,
        "closing": closing,
        "source_side": "arabic",
        "source_owner": "editor",
        **({"label_enabled": True, "label": label} if label else {}),
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


def _ids(field_id: str, token_id: str, source: str) -> dict:
    return {
        "field_id": field_id,
        "tokens": [
            {
                "id": token_id,
                "kind": "math",
                "start": 0,
                "end": len(source),
            }
        ],
    }


def _convert_by_expr(math_object, *, variable_mapping):
    expr = math_object["lines"][0]["chain"][0]["expr"]
    return expr, []


def test_no_equations_returns_empty_projection() -> None:
    mappings = {"x": "س"}
    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english"
    ) as convert:
        result = equation_projection_service.project_document_equations(
            {"node_type": "DocumentObject", "blocks": []}, mappings
        )

    assert result == []
    assert mappings == {"x": "س"}
    convert.assert_not_called()


def test_projects_paragraph_heading_list_and_nested_content() -> None:
    document = {
        "blocks": [
            {
                "id": "paragraph-1",
                "command": r"\paragraph",
                "value": "$س$",
                "inline_ids": _ids("field-p", "math-p", "$س$"),
                "math_objects": [_math("س")],
            },
            {
                "id": "heading-1",
                "command": r"\section",
                "value": r"\[ص\]",
                "inline_ids": _ids("field-h", "math-h", r"\[ص\]"),
                "math_objects": [_math("ص", mode=r"\[", closing=r"\]")],
            },
            {
                "id": "list-1",
                "command": r"\begin{itemize}",
                "closing": r"\end{itemize}",
                "items": [
                    {
                        "id": "item-1",
                        "value": "$ع$",
                        "inline_ids": _ids("field-item", "math-item", "$ع$"),
                        "math_objects": [_math("ع")],
                        "blocks": [
                            {
                                "id": "nested-1",
                                "command": r"\paragraph",
                                "value": "$ل$",
                                "inline_ids": _ids("field-nested", "math-nested", "$ل$"),
                                "math_objects": [_math("ل")],
                            }
                        ],
                    }
                ],
            },
        ]
    }

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english",
        side_effect=_convert_by_expr,
    ):
        result = equation_projection_service.project_document_equations(document, {})

    assert [item["token_id"] for item in result] == [
        "math-p",
        "math-h",
        "math-item",
        "math-nested",
    ]
    assert [item["container"] for item in result] == [
        "paragraph",
        "heading",
        "list_item",
        "paragraph",
    ]
    assert [item["display"] for item in result] == [False, True, False, False]
    assert [item["block_id"] for item in result] == [
        "paragraph-1",
        "heading-1",
        "list-1",
        "nested-1",
    ]


def test_table_math_uses_row_major_sidecar_order_and_caption_math() -> None:
    document = {
        "blocks": [
            {
                "id": "table-1",
                "command": r"\begin{tabular}",
                "closing": r"\end{tabular}",
                "columns": "cc",
                "rows": [["$أ$", "$ب$"], ["$ج$", "plain"]],
                "cell_inline_ids": [
                    [
                        _ids("field-a", "math-a", "$أ$"),
                        _ids("field-b", "math-b", "$ب$"),
                    ],
                    [
                        _ids("field-c", "math-c", "$ج$"),
                        {"field_id": "field-plain", "tokens": []},
                    ],
                ],
                "math_objects": [_math("أ"), _math("ب"), _math("ج")],
                "caption": "$د$",
                "caption_inline_ids": _ids("field-caption", "math-caption", "$د$"),
                "caption_math_objects": [_math("د", label="eq:caption")],
            }
        ]
    }

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english",
        side_effect=_convert_by_expr,
    ):
        result = equation_projection_service.project_document_equations(document, {})

    assert [item["latex"] for item in result] == ["أ", "ب", "ج", "د"]
    assert [item["field_id"] for item in result] == [
        "field-a",
        "field-b",
        "field-c",
        "field-caption",
    ]
    assert [item["container"] for item in result] == [
        "table_cell",
        "table_cell",
        "table_cell",
        "table_caption",
    ]
    assert result[-1]["label"] == "eq:caption"


def test_figure_caption_math_is_discovered() -> None:
    document = {
        "blocks": [
            {
                "id": "figure-1",
                "command": r"\includegraphics",
                "value": "figure.png",
                "caption": "$س$",
                "caption_inline_ids": _ids("field-fig", "math-fig", "$س$"),
                "caption_math_objects": [_math("س")],
            }
        ]
    }

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english",
        side_effect=_convert_by_expr,
    ):
        result = equation_projection_service.project_document_equations(document, {})

    assert len(result) == 1
    assert result[0]["container"] == "figure_caption"
    assert result[0]["token_id"] == "math-fig"


def test_raw_math_is_explicit_and_never_sent_to_burhan() -> None:
    document = {
        "blocks": [
            {
                "id": "paragraph-raw",
                "command": r"\paragraph",
                "value": r"\[raw\]",
                "inline_ids": _ids("field-raw", "math-raw", r"\[raw\]"),
                "math_objects": [
                    {
                        "node_type": "RawMathObject",
                        "label_enabled": True,
                        "label": "eq:raw",
                    }
                ],
            }
        ]
    }

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english"
    ) as convert:
        result = equation_projection_service.project_document_equations(document, {})

    assert result == [
        {
            "block_id": "paragraph-raw",
            "field_id": "field-raw",
            "token_id": "math-raw",
            "container": "paragraph",
            "latex": None,
            "display": True,
            "label": "eq:raw",
            "editable": False,
            "warnings": ["unstructured_math"],
        }
    ]
    convert.assert_not_called()


def test_reverse_mapping_omits_ambiguous_values_and_returns_compact_warnings() -> None:
    mappings = {"x": "س", "X": "س", "y": "ص"}
    document = {
        "blocks": [
            {
                "id": "paragraph-1",
                "command": r"\paragraph",
                "value": "$س$",
                "inline_ids": _ids("field-1", "math-1", "$س$"),
                "math_objects": [_math("س")],
            }
        ]
    }
    captured = {}

    def convert(math_object, *, variable_mapping):
        captured["mapping"] = variable_mapping
        return "x", ["burhan_fallback"]

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english",
        side_effect=convert,
    ):
        result = equation_projection_service.project_document_equations(document, mappings)

    assert captured["mapping"] == {"ص": "y"}
    assert result[0]["warnings"] == [
        "ambiguous_reverse_mapping:س",
        "burhan_fallback",
    ]
    assert mappings == {"x": "س", "X": "س", "y": "ص"}


def test_mapping_mismatch_warns_but_still_projects_equation() -> None:
    document = {
        "blocks": [
            {
                "id": "paragraph-1",
                "command": r"\paragraph",
                "value": "$ع$",
                "inline_ids": _ids("field-1", "math-1", "$ع$"),
                "math_objects": [_math("ع")],
            }
        ]
    }

    with patch(
        "app.services.burhan_reverse_client.convert_math_object_to_english",
        return_value=("q", []),
    ) as convert:
        result = equation_projection_service.project_document_equations(
            document, {"x": "س"}
        )

    assert result[0]["latex"] == "q"
    assert result[0]["warnings"] == ["unmapped_arabic_variable:ع"]
    assert convert.call_args.kwargs["variable_mapping"] == {"س": "x"}


def test_reverse_client_uses_english_tree_contract_and_strips_outer_delimiters() -> None:
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "english_latex": "\\[\nx+1\n\\]",
                "english_json": "{}",
                "variable_mapping": {"س": "x"},
                "warnings": [
                    {"code": "fallback_used", "message": "fallback"},
                    "plain_warning",
                ],
                "status": "ok",
            }

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, path, json):
            captured["path"] = path
            captured["payload"] = json
            return FakeResponse()

    with (
        patch.object(burhan_reverse_client.settings, "burhan_url", "http://burhan"),
        patch.object(burhan_reverse_client.settings, "burhan_model_tier", "heuristic"),
        patch.object(burhan_reverse_client.httpx, "Client", FakeClient),
    ):
        latex, warnings = burhan_reverse_client.convert_math_object_to_english(
            _math("س", mode=r"\[", closing=r"\]", label="eq:one"),
            variable_mapping={"س": "x"},
        )

    assert captured["path"] == "/convert-to-english"
    assert captured["payload"]["variable_mapping"] == {"س": "x"}
    sent_tree = json.loads(captured["payload"]["english_json"])
    assert sent_tree["node_type"] == "MathObject"
    assert sent_tree["lines"][0]["chain"][0]["expr"] == "س"
    assert "source_side" not in sent_tree
    assert "source_owner" not in sent_tree
    assert "label_enabled" not in sent_tree
    assert "label" not in sent_tree
    assert latex == "x+1"
    assert warnings == ["fallback_used", "plain_warning"]


def test_draft_equation_service_returns_revision_context_without_mutating_mappings() -> None:
    article_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    article = SimpleNamespace(equation_mappings={"x": "س"})
    revision = SimpleNamespace(id=revision_id, revision_number=7)
    document = {"node_type": "DocumentObject", "blocks": []}

    with (
        patch(
            "app.services.article_draft_service.assert_editable_author",
            return_value=article,
        ),
        patch(
            "app.services.article_draft_service.get_current_revision",
            return_value=revision,
        ),
        patch(
            "app.services.article_draft_service.read_document",
            return_value=document,
        ),
        patch(
            "app.services.equation_projection_service.project_document_equations",
            return_value=[],
        ) as project,
    ):
        result = draft_equation_service.get_equations(
            SimpleNamespace(), article_id, SimpleNamespace()
        )

    assert result == {
        "revision_id": revision_id,
        "revision_number": 7,
        "document_language": "ar",
        "equation_representation": "canonical_english_latex",
        "variable_mappings": {"x": "س"},
        "equations": [],
    }
    project.assert_called_once_with(document, {"x": "س"})
    assert article.equation_mappings == {"x": "س"}
