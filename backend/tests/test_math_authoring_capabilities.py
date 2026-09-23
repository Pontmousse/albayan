from __future__ import annotations

import os

import httpx
import pytest

from app.services import burhan_client
from app.services.math_authoring_capabilities import (
    INTERNAL_OUTPUT_MACRO_EXAMPLES,
    PARSE_BUILD_ONLY_COMMANDS,
    SAFE_INTERNAL_ENVIRONMENTS,
    advertised_round_trip_commands,
    burhan_verification_cases,
    get_math_authoring_capabilities,
)


def test_math_authoring_contract_is_deterministic_and_isolated() -> None:
    first = get_math_authoring_capabilities()
    second = get_math_authoring_capabilities()

    assert first == second
    first["round_trip_safe"]["raw_operators"].append("@")
    assert "@" not in second["round_trip_safe"]["raw_operators"]
    assert second["canonical_input"] is True
    assert second["representation"] == "canonical_english_latex"


def test_every_advertised_command_has_exactly_one_burhan_verification_case() -> None:
    advertised = advertised_round_trip_commands()
    assert len(advertised) == len(set(advertised))

    labels = [label for _, _, label in burhan_verification_cases()]
    command_labels = [label for label in labels if not label.startswith("environment:")]
    assert set(command_labels) == set(advertised)
    assert len(command_labels) == len(advertised)


def test_every_advertised_environment_has_a_burhan_verification_case() -> None:
    expected = {f"environment:{item['name']}" for item in SAFE_INTERNAL_ENVIRONMENTS}
    actual = {
        label
        for _, _, label in burhan_verification_cases()
        if label.startswith("environment:")
    }
    assert actual == expected


def test_internal_and_parse_only_commands_are_not_advertised_for_authoring() -> None:
    advertised = set(advertised_round_trip_commands())

    assert advertised.isdisjoint(INTERNAL_OUTPUT_MACRO_EXAMPLES)
    assert advertised.isdisjoint(PARSE_BUILD_ONLY_COMMANDS)
    for representative in (r"\foo", r"\partial", r"\text", r"\arsum", r"\butextakween"):
        assert representative not in advertised


def test_contract_pins_reviewed_upstream_revisions_and_reject_examples() -> None:
    contract = get_math_authoring_capabilities()

    assert contract["source_snapshot"]["burhan"]["commit"] == (
        "7ad84b2bdfd4c7eb95c2ad7c584b8e2a93207159"
    )
    assert contract["source_snapshot"]["butex"]["commit"] == (
        "7f55227b4cf368efb26b937c1729ba2e89eee865"
    )
    assert contract["unsupported_or_forbidden"]["explicit_parser_rejection_examples"] == [
        r"x@",
        r"\left(x",
        r"\begin{document}x\end{document}",
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
def test_representative_unsupported_forms_are_rejected_by_live_burhan_parser() -> None:
    base = os.environ["BURHAN_URL"].rstrip("/")
    rejected = get_math_authoring_capabilities()["unsupported_or_forbidden"]
    examples = rejected["explicit_parser_rejection_examples"]

    with httpx.Client(base_url=base, timeout=15.0) as client:
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
