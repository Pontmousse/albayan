import inspect
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from albayan_mcp.api_client import BinaryApiResponse
from albayan_mcp.schemas.document2 import DocumentCommand
from albayan_mcp.tools.drafts import register_draft_tools
from pydantic import TypeAdapter
from tests.test_profile_tools import FakeServer


class DraftToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server = FakeServer()
        register_draft_tools(self.server)
        self.article_id = uuid.uuid4()

    def test_exact_inventory_has_no_session_or_save_tool(self) -> None:
        self.assertEqual(
            set(self.server.tools),
            {
                "get_draft_outline", "get_draft_blocks", "get_draft_references",
                "get_draft_reference_index", "apply_draft_command", "compile_draft",
                "get_compile_status", "get_article_pdf",
            },
        )
        self.assertNotIn("restore_draft", self.server.tools)
        command_description = self.server.tool_options["apply_draft_command"][
            "description"
        ]
        self.assertIn("restore is human-only", command_description)
        self.assertIn("visible in draft history", command_description)

    def test_reference_tools_accept_only_article_id(self) -> None:
        for name in ("get_draft_references", "get_draft_reference_index"):
            with self.subTest(name=name):
                self.assertEqual(
                    list(inspect.signature(self.server.tools[name]).parameters),
                    ["article_id"],
                )

    async def test_get_draft_references_preserves_worker_fields_via_fastapi(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 4,
            "references": [
                {
                    "key": "smith2026",
                    "authors": "A. Smith",
                    "title": "Example paper",
                    "year": "2026",
                    "venue": "Example Journal",
                    "url": "https://example.org/paper",
                    "field_separator": "،",
                }
            ],
        }
        with patch(
            "albayan_mcp.tools.drafts.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_draft_references"](self.article_id)

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/draft/references"
        )
        self.assertEqual(result.revision_number, 4)
        self.assertEqual(result.references[0].field_separator, "،")
        self.assertEqual(result.references[0].key, "smith2026")

    async def test_get_draft_references_allows_empty_catalog(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 1,
            "references": [],
        }
        with patch(
            "albayan_mcp.tools.drafts.api_get_object",
            new=AsyncMock(return_value=response),
        ):
            result = await self.server.tools["get_draft_references"](self.article_id)
        self.assertEqual(result.references, [])

    async def test_get_draft_reference_index_preserves_semantic_index(self) -> None:
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 7,
            "reference_index": {
                "citations": [
                    {
                        "kind": "cite",
                        "block_id": "block-4",
                        "field_id": "field-4",
                        "token_id": "token-cite-1",
                        "keys": ["smith2026", "missing-paper"],
                        "unresolved_keys": ["missing-paper"],
                    }
                ],
                "cross_references": [
                    {
                        "kind": "ref",
                        "ref_command": "ref",
                        "block_id": "block-5",
                        "field_id": "field-5",
                        "token_id": "token-ref-1",
                        "keys": ["fig:overview"],
                        "unresolved_keys": [],
                    },
                    {
                        "kind": "ref",
                        "ref_command": "eqref",
                        "block_id": "block-6",
                        "field_id": "field-6",
                        "token_id": "token-ref-2",
                        "keys": ["eq:missing"],
                        "unresolved_keys": ["eq:missing"],
                    },
                ],
                "labels": [
                    {
                        "key": "fig:overview",
                        "kind": "fig",
                        "caption": "Overview",
                        "number": 1,
                        "block_id": "figure-1",
                    },
                    {
                        "key": "tab:data",
                        "kind": "tab",
                        "caption": "Data",
                        "number": 1,
                        "block_id": "table-1",
                    },
                    {
                        "key": "eq:energy",
                        "kind": "eq",
                        "caption": "",
                        "number": 1,
                        "block_id": "block-3",
                        "field_id": "field-3",
                        "token_id": "token-math-1",
                    },
                ],
                "unresolved": {
                    "citation_keys": ["missing-paper"],
                    "cross_reference_keys": ["eq:missing"],
                },
            },
        }
        with patch(
            "albayan_mcp.tools.drafts.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await self.server.tools["get_draft_reference_index"](
                self.article_id
            )

        get.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/draft/reference-index"
        )
        index = result.reference_index
        self.assertEqual(index.citations[0].token_id, "token-cite-1")
        self.assertEqual(index.cross_references[1].ref_command, "eqref")
        self.assertEqual(index.labels[2].field_id, "field-3")
        self.assertEqual(index.unresolved.citation_keys, ["missing-paper"])
        self.assertEqual(index.unresolved.cross_reference_keys, ["eq:missing"])

    async def test_command_forwards_revision_and_idempotency_id(self) -> None:
        command_id = uuid.uuid4()
        command = TypeAdapter(DocumentCommand).validate_python(
            {"op": "remove_block", "block_id": "block_1"}
        )
        response = {
            "ok": True, "revision_id": str(uuid.uuid4()), "revision_number": 3,
            "document_hash": "a" * 64, "actor_type": "agent", "reason": "ai_edit",
            "document": {"blocks": []}, "affected_block_ids": ["block_1"],
        }
        with patch(
            "albayan_mcp.tools.drafts.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            result = await self.server.tools["apply_draft_command"](
                self.article_id, command_id, 2, command
            )
        post.assert_awaited_once_with(
            f"/api/v1/articles/{self.article_id}/draft/commands",
            json={"command_id": str(command_id), "base_revision": 2,
                  "command": {"op": "remove_block", "block_id": "block_1"}},
        )
        self.assertEqual(result.revision_number, 3)

    async def test_compile_has_no_client_latex_or_hash(self) -> None:
        response = {
            "status": "processing", "compile_id": str(uuid.uuid4()),
            "revision_id": str(uuid.uuid4()), "revision_number": 4,
            "pdf_ready": False, "error": None,
        }
        with patch(
            "albayan_mcp.tools.drafts.api_post_object",
            new=AsyncMock(return_value=response),
        ) as post:
            await self.server.tools["compile_draft"](self.article_id)
        post.assert_awaited_once_with(f"/api/v1/articles/{self.article_id}/draft/compile")

    async def test_pdf_reports_immutable_draft_provenance(self) -> None:
        compile_id = str(uuid.uuid4())
        response = BinaryApiResponse(
            content=b"%PDF-test", content_type="application/pdf",
            headers={"x-albayan-compile-id": compile_id,
                     "x-albayan-draft-revision": "7"},
        )
        with patch(
            "albayan_mcp.tools.drafts.api_get_bytes",
            new=AsyncMock(return_value=response),
        ):
            result = await self.server.tools["get_article_pdf"](self.article_id)
        self.assertEqual(result.meta, {"compile_id": compile_id, "draft_revision": "7"})


if __name__ == "__main__":
    unittest.main()
