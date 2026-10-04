"""Host reader readiness is distinct from enabling canonical-v2 authoring."""

import json
import unittest
from copy import deepcopy
from pathlib import Path

from pydantic import ValidationError

from app.schemas.document2 import DocumentMathObjectJson
from app.schemas.draft_command import DocumentMathAuthoringInlineToken
from app.schemas.math_authoring import MathAuthoringCapabilitiesRead
from app.services.math_authoring_capabilities import get_math_authoring_capabilities


FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "fixtures"
CONTRACT = json.loads((FIXTURES / "math-authoring-contract-v2.json").read_text())


class CanonicalMathContractTests(unittest.TestCase):
    def test_design_fixtures_validate_and_preserve_exact_wire_shape(self):
        for case in CONTRACT["valid_examples"]:
            with self.subTest(case=case["id"]):
                value = DocumentMathObjectJson.model_validate_json(json.dumps(case["payload"]))
                self.assertEqual(value.model_dump(exclude_unset=True), case["payload"])

    def test_invalid_fixtures_fail(self):
        for case in CONTRACT["invalid_examples"]:
            with self.subTest(case=case["id"]), self.assertRaises(ValidationError):
                DocumentMathObjectJson.model_validate(case["payload"])

    def test_compact_profile_is_optional_exact_and_not_emitted_for_legacy(self):
        legacy = {"kind": "math", "latex": "x"}
        self.assertEqual(DocumentMathAuthoringInlineToken.model_validate(legacy).model_dump(exclude_unset=True), legacy)
        proposed = CONTRACT["future_compact_request"]
        self.assertEqual(DocumentMathAuthoringInlineToken.model_validate(proposed).model_dump(exclude_unset=True), proposed)
        for bad in [None, "", "legacy", "canonical-v3", False, 2]:
            with self.subTest(profile=bad), self.assertRaises(ValidationError):
                DocumentMathAuthoringInlineToken.model_validate({**legacy, "authoring_profile": bad})

    def test_metadata_in_deep_ast_requires_root_profile(self):
        atom = {"node_type": "CharObject", "expr": "س", "canonical_atom": {"kind": "variable", "name": "x"}}
        chain = {"node_type": "ChainClass", "chain": [atom]}
        containers = [
            {"node_type": "CharObject", "expr": "a", "superscript": chain},
            {"node_type": "CharObject", "expr": "a", "subscript": chain},
            {"node_type": "DelimiterObject", "inner_expr": chain},
            {"node_type": "CommandObject", "name": r"\frac", "mandatory_args": [chain]},
            {"node_type": "CommandObject", "name": r"\sqrt", "optional_args": [chain]},
            {"node_type": "EnvObject", "lines": [chain]},
        ]
        for node in containers:
            root = {"node_type": "MathObject", "math_mode": "$", "closing": "$", "lines": [{"node_type": "ChainClass", "chain": [node]}]}
            with self.subTest(node=node), self.assertRaises(ValidationError):
                DocumentMathObjectJson.model_validate(root)
            DocumentMathObjectJson.model_validate({**root, "authoring_profile": "canonical-v2"})

    def test_bounded_identity_and_placement(self):
        root = deepcopy(CONTRACT["valid_examples"][1]["payload"])
        node = root["lines"][0]["chain"][0]
        for name in ["", "x+y", "x1", "س", "x\n", "a" * 65, 1]:
            node["canonical_atom"] = {"kind": "variable", "name": name}
            with self.subTest(name=name), self.assertRaises(ValidationError):
                DocumentMathObjectJson.model_validate(root)
        node["canonical_atom"] = {"kind": "variable", "name": "a" * 64}
        DocumentMathObjectJson.model_validate(root)
        for kind in ["NumberObject", "DelimiterObject", "EnvObject", "ChainClass", "MathObject", "OperatorObject"]:
            node["node_type"] = kind
            with self.subTest(node_type=kind), self.assertRaises(ValidationError):
                DocumentMathObjectJson.model_validate(root)
        node["node_type"] = "OperatorObject"
        node["canonical_atom"] = {"kind": "operator", "name": r"\backslash"}
        DocumentMathObjectJson.model_validate(root)

    def test_wrapper_provenance_is_not_a_general_command_override(self):
        root = deepcopy(CONTRACT["valid_examples"][1]["payload"])
        node = {"node_type": "CommandObject", "name": r"\boldarabic", "mandatory_args": [{"node_type": "ChainClass", "chain": []}], "canonical_command": r"\mathbf"}
        root["lines"][0]["chain"] = [node]
        for bad in [r"\mathbf", r"\frac", r"\ad", "arbitrary"]:
            node["name"] = bad
            with self.subTest(name=bad), self.assertRaises(ValidationError):
                DocumentMathObjectJson.model_validate(root)
        node["name"] = r"\boldarabic"
        node["optional_args"] = [{"node_type": "ChainClass", "chain": []}]
        with self.assertRaises(ValidationError):
            DocumentMathObjectJson.model_validate(root)
        node["optional_args"] = []
        node["canonical_command"] = None
        with self.assertRaises(ValidationError):
            DocumentMathObjectJson.model_validate(root)

    def test_legacy_commands_and_glyphs_are_not_reclassified(self):
        root = deepcopy(CONTRACT["valid_examples"][0]["payload"])
        root["lines"][0]["chain"] += [
            {"node_type": "CommandObject", "name": name, "mandatory_args": []}
            for name in [r"\unit", r"\boldarabic", r"\mathbf", r"\diwani", r"\mathtt", r"\mathsf"]
        ]
        self.assertEqual(DocumentMathObjectJson.model_validate(root).model_dump(exclude_unset=True), root)

    def test_capability_reader_accepts_v2_but_live_contract_stays_v1(self):
        actual = get_math_authoring_capabilities()
        frozen = json.loads((FIXTURES / "math-authoring-capabilities-v1.json").read_text())
        self.assertEqual(actual, frozen)
        self.assertEqual(actual["contract_version"], 1)
        MathAuthoringCapabilitiesRead.model_validate(actual)
        future = {**actual, "contract_version": 2, "preferred_submission": {"profile": "canonical-v2"}}
        MathAuthoringCapabilitiesRead.model_validate(future)
        with self.assertRaises(ValidationError):
            MathAuthoringCapabilitiesRead.model_validate({**future, "contract_version": 3})


if __name__ == "__main__":
    unittest.main()
