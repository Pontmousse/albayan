from albayan_dev_mcp.sanitize import sanitize


def test_sanitize_redacts_secret_keys_and_bearer_values() -> None:
    value = {
        "token": "abc",
        "nested": {"authorization": "Bearer abc.def", "message": "Bearer qwerty"},
        "safe": "ok",
    }
    assert sanitize(value) == {
        "token": "[REDACTED]",
        "nested": {"authorization": "[REDACTED]", "message": "Bearer [REDACTED]"},
        "safe": "ok",
    }
