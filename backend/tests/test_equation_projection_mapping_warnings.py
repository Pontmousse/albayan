from app.services import equation_mapping_service, equation_projection_service


def _math_with_arabic_chars(*chars: str) -> dict:
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
                        "name": r"\text",
                        "optional_args": [],
                        "mandatory_args": [
                            {
                                "node_type": "ChainClass",
                                "chain": [
                                    {"node_type": "CharObject", "expr": char}
                                ],
                            }
                        ],
                    }
                    for char in chars
                ],
            }
        ],
    }


def _warnings(math_object: dict, mappings: dict[str, str]) -> list[str]:
    reverse_mapping, ambiguous_values = (
        equation_mapping_service.invert_unique_equation_mappings(mappings)
    )
    return equation_projection_service._mapping_warnings(
        math_object,
        reverse_mapping,
        ambiguous_values,
    )


def test_wrapped_mapping_values_do_not_emit_false_unmapped_warnings() -> None:
    math_object = _math_with_arabic_chars("ف", "ت")

    warnings = _warnings(
        math_object,
        {
            "f": r"\text{ف}",
            "d": r"\ad",
            "t": r"\text{ت}",
        },
    )

    assert warnings == []


def test_genuinely_unmapped_arabic_char_still_warns() -> None:
    math_object = _math_with_arabic_chars("ع")

    warnings = _warnings(math_object, {"x": r"\text{س}"})

    assert warnings == ["unmapped_arabic_variable:ع"]


def test_distinct_wrappers_with_same_arabic_payload_are_ambiguous() -> None:
    math_object = _math_with_arabic_chars("ب")

    warnings = _warnings(
        math_object,
        {
            "beta_text": r"\text{ب}",
            "beta_takween": r"\butextakween{ب}",
        },
    )

    assert warnings == ["ambiguous_reverse_mapping:ب"]
