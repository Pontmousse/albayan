from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from albayan_mcp import file_download


class _AsyncContext:
    def __init__(self, value=None, error: Exception | None = None) -> None:
        self.value = value
        self.error = error

    async def __aenter__(self):
        if self.error:
            raise self.error
        return self.value

    async def __aexit__(self, *args):
        return False


def _client_for(response: httpx.Response):
    client = MagicMock()
    client.stream.return_value = _AsyncContext(response)
    factory = MagicMock(return_value=_AsyncContext(client))
    return factory, client


class FileDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_downloads_supported_image_without_authorization_header(self) -> None:
        response = httpx.Response(
            200,
            headers={"content-type": "image/png", "content-length": "8"},
            content=b"png-data",
        )
        factory, client = _client_for(response)
        with patch.object(
            file_download, "_assert_public_host", new=AsyncMock()
        ), patch.object(file_download.httpx, "AsyncClient", factory):
            result = await file_download.download_client_image(
                "https://files.example/image",
                declared_content_type="image/png",
            )

        self.assertEqual(result.content, b"png-data")
        self.assertEqual(result.filename, "upload.png")
        headers = client.stream.call_args.kwargs["headers"]
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("authorization", headers)

    async def test_rejects_non_https_and_embedded_credentials(self) -> None:
        for url in (
            "http://files.example/image",
            "https://user:password@files.example/image",
            "https://files.example/image#fragment",
        ):
            with self.subTest(url=url), self.assertRaises(RuntimeError):
                await file_download.download_client_image(
                    url,
                    declared_content_type="image/png",
                )

    async def test_public_host_check_rejects_private_or_mixed_dns_results(self) -> None:
        rows = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]
        with patch.object(
            file_download.asyncio,
            "to_thread",
            new=AsyncMock(return_value=rows),
        ):
            with self.assertRaises(RuntimeError):
                await file_download._assert_public_host("files.example", 443)

    async def test_rejects_redirects_oversized_empty_and_unsupported_files(self) -> None:
        cases = [
            httpx.Response(302, headers={"location": "https://other.example"}),
            httpx.Response(
                200,
                headers={
                    "content-type": "image/png",
                    "content-length": str(file_download.MAX_IMAGE_BYTES + 1),
                },
                content=b"x",
            ),
            httpx.Response(200, headers={"content-type": "image/png"}, content=b""),
            httpx.Response(200, headers={"content-type": "text/html"}, content=b"x"),
        ]
        for response in cases:
            factory, _ = _client_for(response)
            with self.subTest(status=response.status_code), patch.object(
                file_download, "_assert_public_host", new=AsyncMock()
            ), patch.object(file_download.httpx, "AsyncClient", factory):
                with self.assertRaises(RuntimeError):
                    await file_download.download_client_image(
                        "https://files.example/image",
                        declared_content_type=None,
                    )

    async def test_rejects_declared_and_response_mime_mismatch(self) -> None:
        response = httpx.Response(
            200,
            headers={"content-type": "image/jpeg"},
            content=b"image",
        )
        factory, _ = _client_for(response)
        with patch.object(
            file_download, "_assert_public_host", new=AsyncMock()
        ), patch.object(file_download.httpx, "AsyncClient", factory):
            with self.assertRaises(RuntimeError):
                await file_download.download_client_image(
                    "https://files.example/image",
                    declared_content_type="image/png",
                )

    async def test_translates_download_timeout_without_exposing_url(self) -> None:
        client = MagicMock()
        client.stream.return_value = _AsyncContext(
            error=httpx.ReadTimeout("temporary URL with signed secret")
        )
        factory = MagicMock(return_value=_AsyncContext(client))
        with patch.object(
            file_download, "_assert_public_host", new=AsyncMock()
        ), patch.object(file_download.httpx, "AsyncClient", factory):
            with self.assertRaises(RuntimeError) as raised:
                await file_download.download_client_image(
                    "https://files.example/image?signature=private",
                    declared_content_type="image/png",
                )

        self.assertNotIn("private", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
