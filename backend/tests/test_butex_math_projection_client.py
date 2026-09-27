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


def _math(expr: str) -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "closing": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [{"node_type": "CharObject", "expr": expr}],
            }
        ],
    }


def test_projects_math_object_through_private_worker_endpoint() -> None:
    source = _math(r"\text{س}")
    projected = _math("س")
    response = httpx.Response(
        200,
        json={"ok": True, "english_math_object": projected},
    )
    client = _client_for(response)

    with (
        patch.object(butex_worker_client.settings, "butex_worker_url", "http://butex"),
        patch.object(butex_worker_client.settings, "butex_worker_token", "secret"),
        patch.object(butex_worker_client.httpx, "Client", return_value=client),
    ):
        result = butex_worker_client.project_math_object_to_english(source)

    assert result == projected
    args, kwargs = client.__enter__.return_value.post.call_args
    assert args[0] == "/v1/document2/math-object/english"
    assert kwargs["json"] == {"math_object": source}
    assert kwargs["headers"]["Authorization"] == "Bearer secret"


def test_rejects_malformed_english_math_object_success() -> None:
    response = httpx.Response(
        200,
        json={"ok": True, "english_math_object": {"node_type": "ChainClass"}},
    )

    with (
        patch.object(butex_worker_client.settings, "butex_worker_url", "http://butex"),
        patch.object(butex_worker_client.settings, "butex_worker_token", "secret"),
        patch.object(
            butex_worker_client.httpx,
            "Client",
            return_value=_client_for(response),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        butex_worker_client.project_math_object_to_english(_math("س"))

    assert raised.value.status_code == 502
