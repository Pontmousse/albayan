import unittest
from copy import deepcopy
from unittest.mock import patch

from fastapi import HTTPException

from app.services import butex_worker_client
from app.services.math_authoring_guard import reject_dormant_math_authoring


class DormantMathGuardTests(unittest.TestCase):
    def test_guard_reserves_wire_keys_without_parsing_text(self):
        legacy = {"blocks": [{"text": "authoring_profile canonical_atom canonical_command \\mathtt{x}"}]}
        before = deepcopy(legacy)
        reject_dormant_math_authoring(legacy)
        self.assertEqual(legacy, before)
        for field in ["authoring_profile", "canonical_atom", "canonical_command"]:
            for value in [None, "canonical-v2", {}]:
                with self.subTest(field=field, value=value), self.assertRaises(HTTPException) as error:
                    reject_dormant_math_authoring({"blocks": [{"tokens": [{"math_object": {field: value}}]}]})
                self.assertEqual(error.exception.status_code, 422)
                self.assertEqual(error.exception.detail["code"], "math_authoring_profile_unavailable")

    def test_full_document_normalization_stops_before_worker(self):
        document = {"blocks": [{"tokens": [{"math_object": {"node_type": "MathObject", "authoring_profile": "canonical-v2"}}]}]}
        with patch.object(butex_worker_client, "_post") as post, self.assertRaises(HTTPException):
            butex_worker_client.normalize_document(document)
        post.assert_not_called()

    def test_insert_replace_and_metadata_commands_stop_before_worker(self):
        for op in ["insert_inline_token", "replace_inline_token"]:
            for token in [
                {"kind": "math", "latex": "x", "authoring_profile": "canonical-v2"},
                {"kind": "math", "math_object": {"canonical_atom": {"kind": "variable", "name": "x"}}},
            ]:
                with self.subTest(op=op, token=token), patch.object(butex_worker_client, "_post") as post, self.assertRaises(HTTPException):
                    butex_worker_client.apply_document_command({"blocks": []}, {"op": op, "token": token})
                post.assert_not_called()
        # Existing metadata must survive even commands that do not insert math.
        document = {"blocks": [{"math_object": {"canonical_command": r"\mathbf"}}]}
        with patch.object(butex_worker_client, "_post") as post, self.assertRaises(HTTPException):
            butex_worker_client.apply_document_command(document, {"op": "update_document_meta", "title": "عنوان"})
        post.assert_not_called()

    def test_legacy_normalization_and_commands_keep_exact_payload(self):
        document = {"blocks": []}
        command = {"op": "remove_block", "block_id": "b1"}
        with patch.object(butex_worker_client, "_post", return_value={"ok": True, "document": document}) as post:
            self.assertEqual(butex_worker_client.normalize_document(document), document)
            post.assert_called_once_with("/v1/document2/normalize", {"document": document})
            post.reset_mock()
            self.assertEqual(butex_worker_client.apply_document_command(document, command), document)
            post.assert_called_once_with("/v1/document2/commands", {"document": document, "command": command})


if __name__ == "__main__":
    unittest.main()
