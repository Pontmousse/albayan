from __future__ import annotations

import os

import httpx
import pytest

from app.schemas.math_authoring import MathAuthoringCapabilitiesRead
from app.services import burhan_client
from app.services.math_authoring_capabilities import (
    BURHAN_COMMIT,
    BUTEX_COMMIT,
    INTERNAL_OUTPUT_MACRO_EXAMPLES,
    PARSE_BUILD_ONLY_COMMANDS,
    RAW_OPERATORS,
    SAFE_DELIMITERS,
    SAFE_INTERNAL_ENVIRONMENTS,
    SEMANTIC_ROLE_COMMANDS,
    STANDARD_SYMBOL_COMMANDS,
    advertised_round_trip_commands,
    burhan_verification_cases,
    get_math_authoring_capabilities,
)


def test_math_authoring_contract_is_deterministic_schema_valid_and_isolated() -> None:
    first = get_math_authoring_capabilities()
    second = get_math_authoring_capabilities()

    assert first == second
    MathAuthoringCapabilitiesRead.model_validate(second)
    first["round_trip_safe"]["raw_operators"].append("@")
    assert "@" not in second["round_trip_safe"]["raw_operators"]
    assert second["canonical_input"] is True
    assert second["representation"] == "canonical_english_latex"


def test_every_advertised_command_has_exactly_one_burhan_verification_case() -> None:
    advertised = advertised_round_trip_commands()
    assert len(advertised) == len(set(advertised))

    labels = [label for _, _, label in burhan_verification_cases()]
    assert set(advertised).issubset(labels)
    for command in advertised:
        assert labels.count(command) == 1


def test_only_browser_validated_semantic_forms_are_advertised_safe() -> None:
    contract = get_math_authoring_capabilities()
    conventions = contract["preferred_submission"]["semantic_conventions"]
    assert set(conventions) == {
        "transpose", "number_sets", "differential", "named_variable", "unit",
    }
    for symbol in "NZQRCH":
        assert rf"\mathbb{{{symbol}}}" in conventions["number_sets"]
    assert r"\mathbb{D}" not in conventions["number_sets"]
    assert r"\unit" in conventions["unit"]
    assert "atomic multi-character Latin variable" in conventions["named_variable"]
    assert "compound expressions" in conventions["named_variable"]

    semantic_roles = contract["round_trip_safe"]["commands"]["semantic_roles"]
    assert semantic_roles == SEMANTIC_ROLE_COMMANDS
    advertised = set(advertised_round_trip_commands())
    assert {r"\top", r"\mathbb", r"\mathrm", r"\mathsf"}.issubset(advertised)
    assert r"\mathtt" not in advertised
    assert {r"\mathbb", r"\mathrm", r"\mathsf"}.isdisjoint(PARSE_BUILD_ONLY_COMMANDS)
    assert r"\mathtt" in PARSE_BUILD_ONLY_COMMANDS

    mathbb = next(item for item in semantic_roles if item["command"] == r"\mathbb")
    assert mathbb["allowed_args"] == list("NZQRCH")
    differential = next(item for item in semantic_roles if item["command"] == r"\mathrm")
    assert differential["allowed_args"] == ["d"]
    unit = next(item for item in semantic_roles if item["command"] == r"\mathsf")
    assert any("raw /" in item for item in unit["constraints"])
    assert not any(item["command"] == r"\mathtt" for item in semantic_roles)

    examples = {item["latex"] for item in contract["examples"]}
    assert r"\frac{\partial f}{\partial x}" in examples
    assert r"A^\top + T" in examples
    assert r"N + \mathbb{N} + 3\mathsf{N}" in examples
    assert r"d + \frac{\mathrm{d}f}{\mathrm{d}x}" in examples
    assert r"\mathtt{var}_0" not in examples
    assert r"m + 3\mathsf{m}" in examples
    assert r"3\mathsf{m}/\mathsf{s}" in examples
    assert r"\mathtt{velocity} = 3\mathsf{m}/\mathsf{s}" not in examples

    conventions["transpose"] = "changed"
    assert get_math_authoring_capabilities()["preferred_submission"]["semantic_conventions"][
        "transpose"
    ] != "changed"


def test_common_standard_symbols_are_advertised_as_one_general_capability_group() -> None:
    contract = get_math_authoring_capabilities()
    advertised_symbols = contract["round_trip_safe"]["commands"]["standard_symbols"]

    assert advertised_symbols == STANDARD_SYMBOL_COMMANDS
    assert set(STANDARD_SYMBOL_COMMANDS) == {
        r"\alpha",
        r"\beta",
        r"\gamma",
        r"\delta",
        r"\epsilon",
        r"\eta",
        r"\theta",
        r"\lambda",
        r"\mu",
        r"\rho",
        r"\sigma",
        r"\tau",
        r"\phi",
        r"\chi",
        r"\psi",
        r"\omega",
        r"\zeta",
        r"\nabla",
        r"\Delta",
        r"\partial",
    }
    assert set(STANDARD_SYMBOL_COMMANDS).isdisjoint(PARSE_BUILD_ONLY_COMMANDS)


def test_every_advertised_environment_delimiter_operator_and_script_has_a_case() -> None:
    labels = {label for _, _, label in burhan_verification_cases()}

    expected_environments = {
        f"environment:{item['name']}" for item in SAFE_INTERNAL_ENVIRONMENTS
    }
    assert expected_environments.issubset(labels)

    expected_delimiters = {f"delimiter:{index}" for index in range(len(SAFE_DELIMITERS))}
    assert expected_delimiters.issubset(labels)

    expected_raw_operators = {f"raw_operator:{operator}" for operator in RAW_OPERATORS}
    assert expected_raw_operators.issubset(labels)
    assert "scripts:^_" in labels
    assert set(RAW_OPERATORS) == {"+", "-", "=", "*", "/", "<", ">"}


def test_internal_and_parse_only_commands_are_not_advertised_for_authoring() -> None:
    advertised = set(advertised_round_trip_commands())

    assert advertised.isdisjoint(INTERNAL_OUTPUT_MACRO_EXAMPLES)
    assert advertised.isdisjoint(PARSE_BUILD_ONLY_COMMANDS)
    for representative in (r"\foo", r"\text", r"\arsum", r"\butextakween"):
        assert representative not in advertised


def test_contract_pins_reviewed_upstream_revisions_and_reject_examples() -> None:
    contract = get_math_authoring_capabilities()

    assert BURHAN_COMMIT == "396d6c1c0068ad01b2f4a19d4dc411deb2f0af17"
    assert BUTEX_COMMIT == "c751789b248db390ad621abf4d671ce19d2a47ba"
    assert contract["source_snapshot"]["burhan"]["commit"] == BURHAN_COMMIT
    assert contract["source_snapshot"]["butex"]["commit"] == BUTEX_COMMIT
    assert "arabic_latex_parser/arabic_json_normalizer.py" in contract["source_snapshot"]["burhan"]["files"]
    assert "tests/api/test_reverse_command_mappings.py" in contract["source_snapshot"]["burhan"]["files"]
    assert "tests/api/test_standard_math_authoring.py" in contract["source_snapshot"]["burhan"]["files"]
    assert "src/editor/standardCommands.ts" in contract["source_snapshot"]["butex"]["files"]
    assert "test/standard_commands.test.ts" in contract["source_snapshot"]["butex"]["files"]
    assert "test/standard_math_roundtrip.test.ts" in contract["source_snapshot"]["butex"]["files"]
    assert contract["unsupported_or_forbidden"]["explicit_parser_rejection_examples"] == [
        r"x@",
        r"\left(x",
        r"\begin{document}x\end{document}",
    ]
    assert contract["accepted_but_not_round_trip_safe"]["delimiters"] == [
        {
            "left": r"\left.",
            "right": r"\right.",
            "form": r"\left. ... \right.",
            "reason": "Burhan supports the invisible delimiter, but the current BuTeX editor delimiter renderer does not recognize '.'.",
        }
    ]


@pytest.mark.skipif(
    not os.getenv("BURHAN_URL"),
    reason="Set BURHAN_URL to verify the snapshot against the live Burhan conversion path.",
)
def test_every_advertised_form_is_accepted_by_live_albayan_burhan_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the exact client used before Document2 insertion for every whitelist entry."""

    monkeypatch.setattr(burhan_client.settings, "burhan_url", os.environ["BURHAN_URL"])
    monkeypatch.setattr(burhan_client.settings, "burhan_model_tier", "heuristic")

    for latex, display, label in burhan_verification_cases():
        # Burhan's matrix/array/aligned family are math-only environments, not
        # top-level MathObject wrappers. Exercise them inside display math.
        if label.startswith("environment:"):
            latex = rf"\[{latex}\]"

        token, mappings = burhan_client.convert_latex_to_math_token(
            latex,
            display=display,
            label=None,
            mappings={},
        )
        assert token["kind"] == "math", label
        assert token["math_object"]["node_type"] == "MathObject", label
        assert token["math_object"]["source_owner"] == "editor", label
        assert isinstance(mappings, dict), label


@pytest.mark.skipif(
    not os.getenv("BURHAN_URL"),
    reason="Set BURHAN_URL to verify representative parser rejection cases.",
)
def test_representative_malformed_forms_are_rejected_by_live_burhan_parser() -> None:
    base = os.environ["BURHAN_URL"].rstrip("/")
    rejected = get_math_authoring_capabilities()["unsupported_or_forbidden"]

    # A whole-document environment is forbidden by the AI equation-authoring policy,
    # but Burhan's parser is intentionally permissive for otherwise tokenizable LaTeX.
    # Parser-rejection CI should therefore cover malformed syntax only.
    policy_only = {r"\begin{document}x\end{document}"}
    examples = [
        latex
        for latex in rejected["explicit_parser_rejection_examples"]
        if latex not in policy_only
    ]

    with httpx.Client(
        base_url=base,
        timeout=15.0,
        headers=burhan_client._burhan_headers(),
    ) as client:
        for latex in examples:
            response = client.post(
                "/parse-equation",
                json={
                    "full_match": f"${latex}$",
                    "opening": "$",
                    "inner_content": latex,
                    "closing": "$",
                    "side": "english",
                    "output_format": "butex-mathobject-v1",
                },
            )
            assert response.status_code == 422, latex
            assert response.json()["detail"]["code"] == "unsupported_latex"
