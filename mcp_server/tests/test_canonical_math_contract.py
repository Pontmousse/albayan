import json
import sys
import unittest
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from albayan_mcp.schemas.document2 import DocumentCommand, DocumentMathObjectJson
from albayan_mcp.schemas.draft_command import DocumentCommand as DraftCommand


REPOSITORY = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((REPOSITORY / "docs/fixtures/math-authoring-contract-v2.json").read_text())


def without_documentation(value):
    if isinstance(value, dict):
        return {key: without_documentation(item) for key, item in value.items() if key not in {"title", "description"}}
    if isinstance(value, list):
        return [without_documentation(item) for item in value]
    return value


class CanonicalMathMirrorTests(unittest.TestCase):
    def test_shared_fixtures_preserve_or_reject_identically(self):
        sys.path.insert(0, str(REPOSITORY / "backend"))
        try:
            from app.schemas.document2 import DocumentMathObjectJson as BackendMath
        finally:
            sys.path.pop(0)
        for case in CONTRACT["valid_examples"]:
            with self.subTest(case=case["id"]):
                expected = case["payload"]
                for model in [BackendMath, DocumentMathObjectJson]:
                    self.assertEqual(model.model_validate_json(json.dumps(expected)).model_dump(exclude_unset=True), expected)
        for case in CONTRACT["invalid_examples"]:
            for model in [BackendMath, DocumentMathObjectJson]:
                with self.subTest(case=case["id"], model=model), self.assertRaises(ValidationError):
                    model.model_validate(case["payload"])

    def test_compact_and_structured_command_schemas_match_backend(self):
        sys.path.insert(0, str(REPOSITORY / "backend"))
        try:
            from app.schemas.document2 import DocumentCommand as BackendCommand
            from app.schemas.draft_command import DocumentCommand as BackendDraftCommand
        finally:
            sys.path.pop(0)
        for mirror, backend in [(DocumentCommand, BackendCommand), (DraftCommand, BackendDraftCommand)]:
            self.assertEqual(without_documentation(TypeAdapter(mirror).json_schema()), without_documentation(TypeAdapter(backend).json_schema()))

    def test_compact_contract_survives_normal_mcp_command_dump(self):
        payload = {"op": "insert_inline_token", "field_id": "f1", "anchor": {"end": True}, "token": CONTRACT["future_compact_request"]}
        self.assertEqual(TypeAdapter(DraftCommand).validate_python(payload).model_dump(exclude_unset=True), payload)

    def test_registry_is_frozen_in_discovery_schema(self):
        definitions = TypeAdapter(DraftCommand).json_schema()["$defs"]
        for model, key in [("CanonicalSymbolAtom", "symbol_names"), ("CanonicalUnitAtom", "unit_names")]:
            self.assertEqual(definitions[model]["properties"]["name"]["enum"], CONTRACT[key])
        self.assertEqual(definitions["DocumentMathNodeJson"]["properties"]["canonical_command"]["anyOf"][0]["enum"], CONTRACT["canonical_commands"])


if __name__ == "__main__":
    unittest.main()
