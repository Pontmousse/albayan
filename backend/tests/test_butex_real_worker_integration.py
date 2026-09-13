from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from app.services import butex_worker_client


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKER_CLI = (
    REPOSITORY_ROOT
    / "frontend"
    / "node_modules"
    / "@drghaliasri"
    / "butex"
    / "dist"
    / "document2-cli.js"
)
NODE = shutil.which("node")


@unittest.skipUnless(
    NODE and WORKER_CLI.is_file(),
    "BuTeX real-worker test requires Node and frontend dependencies",
)
class BuTeXRealWorkerIntegrationTests(unittest.TestCase):
    worker: subprocess.Popen[bytes]
    worker_url: str
    token = "albayan-integration-test-token"

    @classmethod
    def setUpClass(cls) -> None:
        try:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
        except PermissionError as exc:
            raise unittest.SkipTest(
                "Current environment does not permit a loopback worker server"
            ) from exc

        environment = os.environ.copy()
        environment["PORT"] = str(port)
        environment["BUTEX_WORKER_TOKEN"] = cls.token
        cls.worker_url = f"http://127.0.0.1:{port}"
        cls.worker = subprocess.Popen(
            [str(NODE), str(WORKER_CLI), "--serve", "--host", "127.0.0.1"],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if cls.worker.poll() is not None:
                raise RuntimeError("BuTeX worker exited before becoming healthy")
            try:
                with urllib.request.urlopen(  # noqa: S310 - loopback test server
                    f"{cls.worker_url}/health", timeout=0.2
                ) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.05)
        cls.worker.terminate()
        cls.worker.wait(timeout=2)
        raise RuntimeError("BuTeX worker did not become healthy")

    @classmethod
    def tearDownClass(cls) -> None:
        if not hasattr(cls, "worker") or cls.worker.poll() is not None:
            return
        cls.worker.terminate()
        try:
            cls.worker.wait(timeout=2)
        except subprocess.TimeoutExpired:
            cls.worker.kill()
            cls.worker.wait(timeout=2)

    def _apply(self, document: dict, command: dict) -> dict:
        return butex_worker_client.apply_document_command(document, command)

    def test_fastapi_client_executes_each_command_family(self) -> None:
        with patch.object(
            butex_worker_client.settings, "butex_worker_url", self.worker_url
        ), patch.object(
            butex_worker_client.settings, "butex_worker_token", self.token
        ):
            document = butex_worker_client.normalize_document(
                {"node_type": "DocumentObject", "blocks": []}
            )
            document = self._apply(
                document,
                {
                    "op": "insert_text_block",
                    "kind": "paragraph",
                    "text": "نص أول",
                    "anchor": {"end": True},
                    "metadata": {"source": "agent"},
                },
            )
            paragraph = document["blocks"][0]
            field_id = paragraph["inline_ids"]["field_id"]

            document = self._apply(
                document,
                {
                    "op": "insert_inline_token",
                    "field_id": field_id,
                    "token": {"kind": "text", "text": " مضاف"},
                    "anchor": {"end": True},
                },
            )
            document = self._apply(
                document,
                {
                    "op": "update_document_meta",
                    "title": "عنوان التكامل",
                    "date": {"year": 1448},
                },
            )
            document = self._apply(
                document,
                {
                    "op": "insert_reference",
                    "key": "ref:test",
                    "title": "مرجع اختباري",
                    "anchor": {"end": True},
                },
            )
            document = self._apply(
                document,
                {
                    "op": "insert_list",
                    "ordered": False,
                    "items": ["عنصر أول"],
                    "anchor": {"end": True},
                    "metadata": {"source": "agent"},
                },
            )
            list_block = next(
                block for block in document["blocks"] if block["command"] == "\\begin{itemize}"
            )
            document = self._apply(
                document,
                {
                    "op": "insert_list_item",
                    "list_id": list_block["id"],
                    "text": "عنصر ثانٍ",
                    "anchor": {"end": True},
                },
            )
            document = self._apply(
                document,
                {
                    "op": "insert_table",
                    "rows": [["a"]],
                    "columns": "c",
                    "anchor": {"end": True},
                    "metadata": {"source": "agent"},
                },
            )
            table = next(
                block for block in document["blocks"] if block["command"] == "\\begin{tabular}"
            )
            document = self._apply(
                document,
                {
                    "op": "replace_table_cell",
                    "table_id": table["id"],
                    "row_index": 0,
                    "column_index": 0,
                    "text": "b",
                },
            )
            document = self._apply(
                document,
                {
                    "op": "insert_figure",
                    "asset_id": "figures/test.png",
                    "anchor": {"end": True},
                    "metadata": {"source": "agent"},
                },
            )
            document = self._apply(
                document,
                {
                    "op": "insert_bibliography",
                    "anchor": {"end": True},
                    "metadata": {"source": "agent"},
                },
            )

        self.assertEqual(document["meta"]["title"], "عنوان التكامل")
        self.assertEqual(document["references"][0]["key"], "ref:test")
        self.assertEqual(len(list_block["items"]), 1)
        current_list = next(
            block for block in document["blocks"] if block["id"] == list_block["id"]
        )
        self.assertEqual(len(current_list["items"]), 2)
        current_table = next(
            block for block in document["blocks"] if block["id"] == table["id"]
        )
        self.assertEqual(current_table["rows"], [["b"]])
        self.assertTrue(
            any(block["command"] == "\\begin{thebibliography}" for block in document["blocks"])
        )


if __name__ == "__main__":
    unittest.main()
