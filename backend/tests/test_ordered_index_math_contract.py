"""Document2 math tokens retain ordered-index wrappers without schema extensions."""

import pytest

from app.services.burhan_client import _arabic_math_object


def chain(*nodes):
    return {"node_type": "ChainClass", "chain": list(nodes)}


def number(expr):
    return {"node_type": "NumberObject", "expr": expr}


def mapped_letter(arabic, source):
    return {
        "node_type": "CommandObject",
        "name": r"\text",
        "optional_args": [],
        "mandatory_args": [chain({"node_type": "CharObject", "expr": arabic})],
        "source_latex": source,
    }


def explicit_indices(*atoms):
    return {
        "node_type": "CommandObject",
        "name": r"\mathnormal",
        "optional_args": [],
        "mandatory_args": [chain(*atoms)],
    }


@pytest.mark.parametrize(
    "base,script,expected_count",
    [
        (
            mapped_letter("ت", "T"),
            explicit_indices(number("1"), number("2")),
            2,
        ),
        (
            {"node_type": "CommandObject", "name": r"\butextakween",
             "optional_args": [], "mandatory_args": [chain({"node_type": "CharObject", "expr": "ا"})],
             "source_latex": r"\alpha"},
            explicit_indices(
                mapped_letter("ي", "i"), mapped_letter("ج", "j"),
                mapped_letter("ك", "k"), {"node_type": "OperatorObject", "expr": "،"},
                number("2"), number("3"),
            ),
            6,
        ),
    ],
)
def test_marked_indices_survive_existing_document2_wire_schema(base, script, expected_count):
    base["superscript"] = chain(script)
    tree = {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [chain(base)],
    }
    validated = _arabic_math_object(tree, display=False, label=None)
    saved = validated["lines"][0]["chain"][0]["superscript"]["chain"][0]
    assert saved["name"] == r"\mathnormal"
    assert len(saved["mandatory_args"][0]["chain"]) == expected_count
    assert validated["source_side"] == "arabic"
    assert validated["source_owner"] == "editor"


def test_ordinary_numeric_subscript_is_not_marked():
    base = mapped_letter("س", "x")
    base["subscript"] = chain(number("12"))
    validated = _arabic_math_object(
        {"node_type": "MathObject", "math_mode": "$", "closing": "$",
         "lines": [chain(base)]},
        display=False,
        label=None,
    )
    subscript = validated["lines"][0]["chain"][0]["subscript"]["chain"]
    assert subscript[0]["node_type"] == "NumberObject"
    assert subscript[0]["expr"] == "12"
