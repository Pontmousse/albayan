from __future__ import annotations

from app.services import equation_diagnostic_service


def _editor_math_object() -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "source_side": "arabic",
        "source_owner": "editor",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {
                        "node_type": "CommandObject",
                        "name": "\\butextakween",
                        "optional_args": [],
                        "mandatory_args": [
                            {
                                "node_type": "ChainClass",
                                "chain": [{"node_type": "CharObject", "expr": "ا"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _english_projected_math_object() -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {
                        "node_type": "CommandObject",
                        "name": "\\butextakween",
                        "optional_args": [],
                        "mandatory_args": [
                            {
                                "node_type": "ChainClass",
                                "chain": [{"node_type": "CharObject", "expr": "ا"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_reverse_diagnostic_mirrors_ai_facing_read_pipeline(monkeypatch) -> None:
    editor_math = _editor_math_object()
    projected_math = _english_projected_math_object()
    captured: dict = {}

    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        assert latex == r"\alpha"
        diagnostics.update(
            {
                "canonical_input": {"latex": latex, "display": display},
                "english_json": {"node_type": "MathObject"},
                "arabic_json": {"node_type": "MathObject"},
                "arabic_latex": r"$\butextakween{ا}$",
                "mappings": {r"\alpha": r"\text{\takween{ا}}"},
                "warnings": [],
            }
        )
        return {
            "kind": "math",
            "source": r"$\butextakween{ا}$",
            "math_object": editor_math,
        }, {r"\alpha": r"\text{\takween{ا}}"}

    def fake_normalize(document):
        return document

    def fake_apply(document, command):
        if command["op"] == "insert_text_block":
            return {
                "node_type": "DocumentObject",
                "blocks": [
                    {
                        "id": "block_1",
                        "value": "",
                        "inline_ids": {"field_id": "field_1", "tokens": []},
                    }
                ],
            }
        return {"node_type": "DocumentObject", "blocks": [{"id": "block_1"}]}

    def fake_project(math_object):
        captured["project_input"] = math_object
        return projected_math

    def fake_reverse(math_object, *, variable_mapping, model_tier=None):
        captured["reverse_input"] = math_object
        captured["reverse_mapping"] = variable_mapping
        return r"\alpha", []

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fake_convert,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "normalize_document",
        fake_normalize,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "apply_document_command",
        fake_apply,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "project_math_object_to_english",
        fake_project,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        lambda _math: {"ok": True, "editable": True},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.burhan_reverse_client,
        "convert_math_object_to_english",
        fake_reverse,
    )

    report = equation_diagnostic_service.inspect_equation(
        latex=r"\alpha",
        display=False,
        model_tier="heuristic",
    )

    assert report["ok"] is True
    assert captured["project_input"] == editor_math
    assert captured["reverse_input"] == projected_math
    assert captured["reverse_mapping"] == {r"\text{\takween{ا}}": r"\alpha"}
    reverse_data = report["stages"]["reverse_conversion"]["data"]
    assert reverse_data["canonical_latex"] == r"\alpha"
    assert reverse_data["reverse_mapping"] == {r"\text{\takween{ا}}": r"\alpha"}
    assert reverse_data["ambiguous_mapping_values"] == []
