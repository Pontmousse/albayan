from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
from pydantic import SecretStr

from app.core.revision_summary_config import revision_summary_settings
from app.services import openrouter_client


def _client_for(response: httpx.Response) -> MagicMock:
    client = MagicMock()
    client.__enter__.return_value.post.return_value = response
    client.__exit__.return_value = None
    return client


def _diff() -> dict:
    return {
        "version": 1,
        "changed": True,
        "truncated": False,
        "chunks": [{"kind": "added", "text": "paragraph"}],
    }


def test_openrouter_requests_strict_structured_arabic_summary() -> None:
    summary = {
        "version": 1,
        "items": [
            {"kind": "added", "text": "أضيفت فقرة جديدة."},
            {"kind": "edited", "text": "عُدّل شرح المعادلة."},
        ],
    }
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": json.dumps(summary)}}]},
    )
    client = _client_for(response)

    with patch.object(
        revision_summary_settings, "openrouter_api_key", SecretStr("sk-or-v1-test")
    ), patch.object(
        revision_summary_settings, "openrouter_model", "openrouter/free"
    ), patch.object(openrouter_client.httpx, "Client", return_value=client):
        result = openrouter_client.summarize_revision_diff(_diff())

    assert result == summary
    _, kwargs = client.__enter__.return_value.post.call_args
    body = kwargs["json"]
    assert body["model"] == "openrouter/free"
    assert body["provider"] == {"require_parameters": True}
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["items"]["maxItems"] == 4
    assert schema["properties"]["items"]["items"]["properties"]["kind"]["enum"] == [
        "added",
        "removed",
        "edited",
        "moved",
        "metadata",
        "other",
    ]
    text_description = schema["properties"]["items"]["items"]["properties"]["text"][
        "description"
    ]
    assert "reader-facing Arabic" in text_description
    assert "internal field names" in text_description
    assert json.loads(body["messages"][1]["content"]) == {"diff": _diff()}
    assert kwargs["headers"]["Authorization"] == "Bearer sk-or-v1-test"


def test_openrouter_prompt_hides_machine_or_storage_details_from_readers() -> None:
    prompt = openrouter_client._SYSTEM_PROMPT

    assert "Describe what changed in the article" in prompt
    assert "never how the change is represented, serialized, stored, or implemented" in prompt
    assert "image_id" in prompt
    assert "caption_enabled" in prompt
    assert "centered" in prompt
    assert "label_enabled" in prompt
    assert "assets/..." in prompt
    assert "UUIDs" in prompt
    assert "raw true/false values" in prompt
    assert "Never quote old/new filenames" in prompt
    assert "combine them into one semantic change" in prompt
    assert "final reader-visible effect" in prompt


def test_openrouter_rejects_invalid_schema_output() -> None:
    response = httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "version": 1,
                                "items": [{"kind": "surprise", "text": "x"}],
                            }
                        )
                    }
                }
            ]
        },
    )
    with patch.object(
        revision_summary_settings, "openrouter_api_key", SecretStr("sk-or-v1-test")
    ), patch.object(openrouter_client.httpx, "Client", return_value=_client_for(response)):
        assert openrouter_client.summarize_revision_diff(_diff()) is None


def test_openrouter_missing_key_is_safe_and_does_not_call_network() -> None:
    with patch.object(
        revision_summary_settings, "openrouter_api_key", SecretStr("")
    ), patch.object(openrouter_client.httpx, "Client") as client:
        assert openrouter_client.summarize_revision_diff(_diff()) is None
    client.assert_not_called()


def test_openrouter_timeout_is_safe() -> None:
    client = MagicMock()
    client.__enter__.return_value.post.side_effect = httpx.TimeoutException("slow")
    client.__exit__.return_value = None
    with patch.object(
        revision_summary_settings, "openrouter_api_key", SecretStr("sk-or-v1-test")
    ), patch.object(openrouter_client.httpx, "Client", return_value=client):
        assert openrouter_client.summarize_revision_diff(_diff()) is None
