"""Contract tests for deterministic canonical equation interoperability."""

from __future__ import annotations

from app.services import (
    burhan_client,
    burhan_reverse_client,
    equation_diagnostic_service,
    equation_projection_service,
)
from app.services.burhan_client import CANONICAL_INTEROP_TIER


def _math_token(expr: str = "س") -> dict:
    return {
        "kind": "math",
        "source": f"${expr}$",
        "math_object": {
            "node_type": "MathObject",
            "math_mode": "$",
            "closing": "$",
            "source_side": "arabic",
            "source_owner": "editor",
            "lines": [
                {
                    "node_type": "ChainClass",
                    "chain": [{"node_type": "CharObject", "expr": expr}],
                }
            ],
        },
    }


def test_canonical_interop_tier_is_deterministic() -> None:
    assert CANONICAL_INTEROP_TIER == "heuristic"


def test_convert_canonical_latex_forces_heuristic_tier(monkeypatch) -> None:
    captured: dict = {}

    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        captured["model_tier"] = model_tier
        return _math_token(), {"x": "س"}

    monkeypatch.setattr(burhan_client, "convert_latex_to_math_token", fake_convert)
    monkeypatch.setattr(burhan_client.settings, "burhan_model_tier", "cheap")

    token, mappings = burhan_client.convert_canonical_latex_to_math_object(
        "x",
        display=False,
        label=None,
        mappings={},
    )

    assert token["kind"] == "math"
    assert mappings == {"x": "س"}
    assert captured["model_tier"] == "heuristic"


def test_project_math_object_to_canonical_latex_forces_heuristic_tier(monkeypatch) -> None:
    captured: dict = {}

    def fake_reverse(math_object, *, variable_mapping, model_tier=None):
        captured["model_tier"] = model_tier
        return "x", []

    monkeypatch.setattr(
        burhan_reverse_client, "convert_math_object_to_english", fake_reverse
    )
    monkeypatch.setattr(burhan_reverse_client.settings, "burhan_model_tier", "cheap")

    latex, warnings = burhan_reverse_client.project_math_object_to_canonical_latex(
        _math_token()["math_object"],
        variable_mapping={"س": "x"},
    )

    assert latex == "x"
    assert warnings == []
    assert captured["model_tier"] == "heuristic"


def test_projection_service_uses_canonical_interop_policy_not_settings_default(
    monkeypatch,
) -> None:
    """Production projection must not silently inherit settings.burhan_model_tier."""
    captured: dict = {}
    math_object = _math_token()["math_object"]
    document = {
        "blocks": [
            {
                "id": "paragraph-1",
                "command": r"\paragraph",
                "value": "$س$",
                "inline_ids": {
                    "field_id": "field-1",
                    "tokens": [
                        {"id": "math-1", "kind": "math", "start": 0, "end": 3}
                    ],
                },
                "math_objects": [math_object],
            }
        ]
    }

    def fake_project(raw):
        return raw

    def fake_reverse(math, *, variable_mapping, model_tier=None):
        captured["model_tier"] = model_tier
        captured["variable_mapping"] = variable_mapping
        return "x", []

    monkeypatch.setattr(
        equation_projection_service.butex_worker_client,
        "project_math_object_to_english",
        fake_project,
    )
    def fake_canonical_project(math, *, variable_mapping):
        captured["variable_mapping"] = variable_mapping
        # Production projection must call the canonical wrapper, which itself
        # forces heuristic regardless of settings.burhan_model_tier.
        return fake_reverse(math, variable_mapping=variable_mapping, model_tier="heuristic")

    monkeypatch.setattr(
        equation_projection_service.burhan_reverse_client,
        "project_math_object_to_canonical_latex",
        fake_canonical_project,
    )
    monkeypatch.setattr(
        equation_projection_service.burhan_reverse_client.settings,
        "burhan_model_tier",
        "cheap",
    )

    result = equation_projection_service.project_document_equations(
        document, {"x": "س"}
    )

    assert result[0]["latex"] == "x"
    assert captured["model_tier"] == "heuristic"
    assert captured["variable_mapping"] == {"س": "x"}


def _install_pipeline_with_reverse_latex(monkeypatch, *, reverse_latex: str) -> None:
    input_ast = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {"node_type": "CharObject", "expr": "x"},
                    {"node_type": "CharObject", "expr": "\\leq"},
                    {"node_type": "CharObject", "expr": "y"},
                ],
            }
        ],
    }
    reverse_ast = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {"node_type": "CharObject", "expr": "x"},
                    {"node_type": "CharObject", "expr": "\\geq"},
                    {"node_type": "CharObject", "expr": "y"},
                ],
            }
        ],
    }

    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        assert model_tier == "heuristic"
        ast = reverse_ast if latex == reverse_latex else input_ast
        if diagnostics is not None:
            diagnostics.update(
                {
                    "canonical_input": {"latex": latex, "display": display},
                    "burhan_request": {"model_tier": "heuristic"},
                    "english_json": ast,
                    "arabic_json": {"node_type": "MathObject"},
                    "arabic_latex": "$س$",
                    "mappings": {"x": "س", "y": "ص"},
                    "warnings": [],
                    "resolved_model": None,
                    "duration_ms": 1.0,
                    "editor_math_object": _math_token()["math_object"],
                }
            )
        return _math_token(), {"x": "س", "y": "ص"}

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fake_convert,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "normalize_document",
        lambda document: document,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "apply_document_command",
        lambda document, command: {
            "node_type": "DocumentObject",
            "blocks": [
                {
                    "id": "block_1",
                    "command": "\\paragraph",
                    "value": "",
                    "inline_ids": {"field_id": "field_1", "tokens": []},
                }
            ],
        }
        if command["op"] == "insert_text_block"
        else {"node_type": "DocumentObject", "blocks": [{"id": "block_1"}]},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "project_math_object_to_english",
        lambda math: math,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        lambda math: {"ok": True, "editable": True},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.burhan_reverse_client,
        "convert_math_object_to_english",
        lambda math, *, variable_mapping, model_tier=None: (reverse_latex, []),
    )


def test_lossy_operator_flip_fails_round_trip_equivalence_despite_http_ok(
    monkeypatch,
) -> None:
    _install_pipeline_with_reverse_latex(monkeypatch, reverse_latex=r"x \geq y")

    report = equation_diagnostic_service.inspect_equation(
        latex=r"x \leq y",
        display=False,
        model_tier="heuristic",
    )

    assert report["stages"]["reverse_conversion"]["ok"] is True
    equivalence = report["stages"]["round_trip_equivalence"]
    assert equivalence["available"] is True
    assert equivalence["ok"] is False
    assert equivalence["authoritative"] is True
    assert report["ok"] is False


def test_case_collapsing_variable_fails_round_trip_equivalence(monkeypatch) -> None:
    input_ast = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {"node_type": "CharObject", "expr": "x"},
                    {"node_type": "CharObject", "expr": "+"},
                    {"node_type": "CharObject", "expr": "X"},
                ],
            }
        ],
    }
    collapsed_ast = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {"node_type": "CharObject", "expr": "x"},
                    {"node_type": "CharObject", "expr": "+"},
                    {"node_type": "CharObject", "expr": "x"},
                ],
            }
        ],
    }

    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        ast = collapsed_ast if latex == "x + x" else input_ast
        if diagnostics is not None:
            diagnostics.update(
                {
                    "canonical_input": {"latex": latex, "display": display},
                    "burhan_request": {"model_tier": "heuristic"},
                    "english_json": ast,
                    "arabic_json": {"node_type": "MathObject"},
                    "arabic_latex": "$س$",
                    "mappings": {"x": "س", "X": "س"},
                    "warnings": [],
                    "resolved_model": None,
                    "duration_ms": 1.0,
                    "editor_math_object": _math_token()["math_object"],
                }
            )
        return _math_token(), {"x": "س", "X": "س"}

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fake_convert,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "normalize_document",
        lambda document: document,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "apply_document_command",
        lambda document, command: {
            "node_type": "DocumentObject",
            "blocks": [
                {
                    "id": "block_1",
                    "command": "\\paragraph",
                    "value": "",
                    "inline_ids": {"field_id": "field_1", "tokens": []},
                }
            ],
        }
        if command["op"] == "insert_text_block"
        else {"node_type": "DocumentObject", "blocks": [{"id": "block_1"}]},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "project_math_object_to_english",
        lambda math: math,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        lambda math: {"ok": True, "editable": True},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.burhan_reverse_client,
        "convert_math_object_to_english",
        lambda math, *, variable_mapping, model_tier=None: ("x + x", []),
    )

    report = equation_diagnostic_service.inspect_equation(
        latex="x + X",
        display=False,
        model_tier="heuristic",
    )

    assert report["stages"]["reverse_conversion"]["ok"] is True
    assert report["stages"]["round_trip_equivalence"]["ok"] is False
    assert report["ok"] is False


def test_formatting_only_subscript_difference_is_round_trip_equivalent(
    monkeypatch,
) -> None:
    """x_1 vs x_{1} must not fail when normalized English ASTs match."""
    shared_ast = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [
                    {
                        "node_type": "CharObject",
                        "expr": "x",
                        "subscript": {
                            "node_type": "ChainClass",
                            "chain": [{"node_type": "CharObject", "expr": "1"}],
                        },
                    }
                ],
            }
        ],
    }

    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        if diagnostics is not None:
            diagnostics.update(
                {
                    "canonical_input": {"latex": latex, "display": display},
                    "burhan_request": {"model_tier": "heuristic"},
                    "english_json": shared_ast,
                    "arabic_json": {"node_type": "MathObject"},
                    "arabic_latex": "$س$",
                    "mappings": {"x": "س"},
                    "warnings": [],
                    "resolved_model": None,
                    "duration_ms": 1.0,
                    "editor_math_object": _math_token()["math_object"],
                }
            )
        return _math_token(), {"x": "س"}

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fake_convert,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "normalize_document",
        lambda document: document,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "apply_document_command",
        lambda document, command: {
            "node_type": "DocumentObject",
            "blocks": [
                {
                    "id": "block_1",
                    "command": "\\paragraph",
                    "value": "",
                    "inline_ids": {"field_id": "field_1", "tokens": []},
                }
            ],
        }
        if command["op"] == "insert_text_block"
        else {"node_type": "DocumentObject", "blocks": [{"id": "block_1"}]},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "project_math_object_to_english",
        lambda math: math,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        lambda math: {"ok": True, "editable": True},
    )
    monkeypatch.setattr(
        equation_diagnostic_service.burhan_reverse_client,
        "convert_math_object_to_english",
        lambda math, *, variable_mapping, model_tier=None: (r"x_{1}", []),
    )

    report = equation_diagnostic_service.inspect_equation(
        latex="x_1",
        display=False,
        model_tier="heuristic",
    )

    assert report["stages"]["reverse_conversion"]["data"]["canonical_latex"] == r"x_{1}"
    assert report["stages"]["round_trip_equivalence"]["ok"] is True
    assert report["ok"] is True


def test_normalize_math_ast_drops_null_placeholders() -> None:
    left = {
        "node_type": "CharObject",
        "expr": "x",
        "superscript": None,
        "subscript": None,
    }
    right = {"node_type": "CharObject", "expr": "x"}
    assert burhan_client.normalize_english_math_ast(left) == (
        burhan_client.normalize_english_math_ast(right)
    )
