import unittest
import uuid
from unittest.mock import AsyncMock, patch

from albayan_mcp.tools.drafts import register_draft_tools
from tests.test_profile_tools import FakeServer


class EmptyReferenceIntrospectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_reference_index_is_a_successful_read(self) -> None:
        server = FakeServer()
        register_draft_tools(server)
        article_id = uuid.uuid4()
        response = {
            "revision_id": str(uuid.uuid4()),
            "revision_number": 1,
            "reference_index": {
                "citations": [],
                "cross_references": [],
                "labels": [],
                "unresolved": {
                    "citation_keys": [],
                    "cross_reference_keys": [],
                },
            },
        }

        with patch(
            "albayan_mcp.tools.drafts.api_get_object",
            new=AsyncMock(return_value=response),
        ) as get:
            result = await server.tools["get_draft_reference_index"](article_id)

        get.assert_awaited_once_with(
            f"/api/v1/articles/{article_id}/draft/reference-index"
        )
        self.assertEqual(result.reference_index.citations, [])
        self.assertEqual(result.reference_index.cross_references, [])
        self.assertEqual(result.reference_index.labels, [])
        self.assertEqual(result.reference_index.unresolved.citation_keys, [])
        self.assertEqual(result.reference_index.unresolved.cross_reference_keys, [])


if __name__ == "__main__":
    unittest.main()
