"""Plan C: plain mapping keys must not turn atomic prose into variables."""

from app.services.equation_projection_service import (
    _arabic_char_values,
    _mapping_warnings,
    _unresolved_atomic_warnings,
)


def _atomic(name: str, expr: str, source: str | None = None) -> dict:
    node = {
        "node_type": "CommandObject",
        "name": name,
        "optional_args": [],
        "mandatory_args": [{
            "node_type": "ChainClass",
            "chain": [{"node_type": "CharObject", "expr": expr}],
        }],
    }
    if source is not None:
        node["source_latex"] = source
    return node


def test_edited_operator_and_sentence_are_not_unmapped_variables() -> None:
    math = {
        "node_type": "MathObject",
        "lines": [{"node_type": "ChainClass", "chain": [
            _atomic(r"\operatorname", "التشتت"),
            _atomic(r"\text", "بشرط تحقق"),
            _atomic(r"\mathtt", "السرعة"),
        ]}],
    }
    assert _arabic_char_values(math) == []
    assert _mapping_warnings(math, {}, set()) == []


def test_atomic_scripts_and_neighboring_variables_still_get_warnings() -> None:
    operator = _atomic(r"\operatorname", "التشتت")
    operator["superscript"] = {
        "node_type": "ChainClass",
        "chain": [{"node_type": "CharObject", "expr": "س"}],
    }
    math = {"node_type": "MathObject", "lines": [{
        "node_type": "ChainClass",
        "chain": [operator, {"node_type": "CharObject", "expr": "ص"}],
    }]}
    assert _arabic_char_values(math) == ["س", "ص"]


def test_original_variable_source_remains_distinct_from_literal_text() -> None:
    math = {"node_type": "MathObject", "lines": [{
        "node_type": "ChainClass",
        "chain": [
            _atomic(r"\text", "س", source="x"),
            _atomic(r"\text", "بشرط تحقق"),
        ],
    }]}
    assert _arabic_char_values(math) == []


def test_unresolved_heuristic_fallback_is_visible_on_readback() -> None:
    math = {"node_type": "MathObject", "lines": [{
        "node_type": "ChainClass",
        "chain": [
            _atomic(r"\operatorname", "Var", source=r"\operatorname{Var}"),
            _atomic(r"\text", "subject to", source=r"\text{subject to}"),
            _atomic(r"\operatorname", "التباين", source=r"\operatorname{Var}"),
            _atomic(r"\mathtt", "velocity", source=r"\mathtt{velocity}"),
        ],
    }]}
    assert _unresolved_atomic_warnings(math) == [
        "unresolved_atomic_translation:Var",
        "unresolved_atomic_translation:subject to",
        "unresolved_atomic_translation:velocity",
    ]
