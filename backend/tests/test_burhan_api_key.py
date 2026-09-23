from __future__ import annotations

from app.services import burhan_client


def test_burhan_headers_are_empty_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("BURHAN_API_KEY", raising=False)

    assert burhan_client._burhan_headers() == {}


def test_burhan_headers_use_bearer_api_key(monkeypatch) -> None:
    monkeypatch.setenv("BURHAN_API_KEY", "test-secret")

    assert burhan_client._burhan_headers() == {
        "Authorization": "Bearer test-secret"
    }


def test_burhan_headers_ignore_blank_api_key(monkeypatch) -> None:
    monkeypatch.setenv("BURHAN_API_KEY", "   ")

    assert burhan_client._burhan_headers() == {}
