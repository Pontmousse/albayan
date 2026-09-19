from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.services import butex_worker_client


def _client_for(response: httpx.Response) -> MagicMock:
    client = MagicMock()
    client.__enter__.return_value.post.return_value = response
    client.__exit__.return_value = None
    return client


def test_diff_documents_uses_document2_diff_contract() -> None:
    before = {"node_type": "DocumentObject", "blocks": []}
    after = {"node_type": "DocumentObject", "blocks": [{"id": "p1"}]}
    response = httpx.Response(
        200,
        json={
            "ok": True,
            "diff": {
                "version": 1,
                "changed": True,
                "truncated": False,
                "chunks": [
                    {"kind": "context", "text": '"blocks":['},
                    {"kind": "added", "text": '{"id":"p1"}'},
                ],
            },
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
        result = butex_worker_client.diff_documents(before, after)

    assert result["version"] == 1
    assert result["changed"] is True
    args, kwargs = client.__enter__.return_value.post.call_args
    assert args[0] == "/v1/document2/diff"
    assert kwargs["json"] == {"before": before, "after": after}


@pytest.mark.parametrize(
    "bad_diff",
    [
        {"version": 2, "changed": True, "truncated": False, "chunks": []},
        {"version": 1, "changed": "yes", "truncated": False, "chunks": []},
        {
            "version": 1,
            "changed": True,
            "truncated": False,
            "chunks": [{"kind": "edited", "text": "x"}],
        },
        {
            "version": 1,
            "changed": False,
            "truncated": False,
            "chunks": [{"kind": "context", "text": "x"}],
        },
    ],
)
def test_diff_documents_rejects_malformed_success(bad_diff: dict) -> None:
    response = httpx.Response(200, json={"ok": True, "diff": bad_diff})
    with patch.object(
        butex_worker_client.settings, "butex_worker_url", "http://butex"
    ), patch.object(
        butex_worker_client.settings, "butex_worker_token", "secret"
    ), patch.object(
        butex_worker_client.httpx, "Client", return_value=_client_for(response)
    ), pytest.raises(HTTPException) as raised:
        butex_worker_client.diff_documents({"blocks": []}, {"blocks": []})

    assert raised.value.status_code == 502
