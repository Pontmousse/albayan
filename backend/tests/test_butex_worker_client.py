from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import httpx
from fastapi import HTTPException

from app.services import butex_worker_client


def _client_for(response: httpx.Response) -> MagicMock:
    client = MagicMock()
    client.__enter__.return_value.post.return_value = response
    client.__exit__.return_value = None
    return client


class BuTeXWorkerClientTests(unittest.TestCase):
    def test_exports_document_with_latex_and_assets(self) -> None:
        response = httpx.Response(
            200,
            json={
                "ok": True,
                "latex": "\\documentclass{article}",
                "asset_ids": ["assets/a.png"],
            },
        )
        client = _client_for(response)

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=client
        ):
            result = butex_worker_client.export_document({"blocks": []})

        self.assertEqual(result, ("\\documentclass{article}", ["assets/a.png"]))
        args, kwargs = client.__enter__.return_value.post.call_args
        self.assertEqual(args[0], "/v1/document2/export")
        self.assertEqual(kwargs["json"], {"document": {"blocks": []}})

    def test_preserves_bounded_export_validation_issues(self) -> None:
        response = httpx.Response(
            422,
            json={
                "ok": False,
                "error": {
                    "code": "invalid_document",
                    "message": "Document validation failed",
                    "issues": [
                        {
                            "code": "empty_image",
                            "path": "blocks[0]",
                            "blockId": "block_1",
                            "private": "not-forwarded",
                        }
                    ],
                },
            },
        )

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=_client_for(response)
        ), self.assertRaises(HTTPException) as raised:
            butex_worker_client.export_document({"blocks": []})

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(
            raised.exception.detail["issues"],
            [
                {
                    "code": "empty_image",
                    "path": "blocks[0]",
                    "blockId": "block_1",
                }
            ],
        )

    def test_rejects_malformed_export_success(self) -> None:
        response = httpx.Response(
            200,
            json={"ok": True, "latex": "tex", "asset_ids": ["assets/a.png", 3]},
        )
        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=_client_for(response)
        ), self.assertRaises(HTTPException) as raised:
            butex_worker_client.export_document({"blocks": []})

        self.assertEqual(raised.exception.status_code, 502)

    def test_posts_document_command_with_private_headers(self) -> None:
        response = httpx.Response(
            200,
            json={
                "ok": True,
                "document": {"node_type": "DocumentObject", "blocks": []},
            },
        )
        client = _client_for(response)

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=client
        ):
            document = butex_worker_client.apply_document_command(
                {"node_type": "DocumentObject", "blocks": []},
                {"op": "remove_block", "block_id": "block_1"},
            )

        self.assertEqual(document, {"node_type": "DocumentObject", "blocks": []})
        client.__enter__.return_value.post.assert_called_once()
        args, kwargs = client.__enter__.return_value.post.call_args
        self.assertEqual(args[0], "/v1/document2/commands")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["headers"]["X-Request-ID"], "albayan-backend")

    def test_preserves_structured_worker_error(self) -> None:
        response = httpx.Response(
            422,
            json={
                "ok": False,
                "error": {
                    "code": "block_not_found",
                    "message": "Document block was not found: block_9",
                },
            },
        )

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=_client_for(response)
        ), self.assertRaises(HTTPException) as raised:
            butex_worker_client.outline_document({"blocks": []})

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(
            raised.exception.detail,
            {
                "code": "block_not_found",
                "message": "Document block was not found: block_9",
            },
        )

    def test_maps_timeout_to_504(self) -> None:
        post = MagicMock(side_effect=httpx.TimeoutException("slow"))
        client = MagicMock()
        client.__enter__.return_value.post = post
        client.__exit__.return_value = None

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=client
        ), self.assertRaises(HTTPException) as raised:
            butex_worker_client.normalize_document({"blocks": []})

        self.assertEqual(raised.exception.status_code, 504)

    def test_rejects_invalid_success_body(self) -> None:
        response = httpx.Response(200, json={"ok": True, "outline": []})

        with patch.object(
            butex_worker_client.settings, "butex_worker_url", "http://butex"
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", "secret"
        ), patch.object(
            butex_worker_client.httpx, "Client", return_value=_client_for(response)
        ), self.assertRaises(HTTPException) as raised:
            butex_worker_client.normalize_document({"blocks": []})

        self.assertEqual(raised.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
