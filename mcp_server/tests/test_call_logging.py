from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from albayan_mcp.api_client import BackendApiError
from albayan_mcp.call_logging import (
    INPUT_LIMIT_BYTES,
    McpCallLoggingMiddleware,
    _post_log,
    sanitize_snapshot,
)
from albayan_mcp.server import create_server


def _context(method: str = "tools/call", params=None):
    return SimpleNamespace(
        method=method,
        params=params
        or {
            "name": "apply_session_command",
            "arguments": {
                "article_id": "article_1",
                "command": {"op": "insert_text_block", "token": "ordinary"},
            },
        },
    )


class SnapshotSanitizationTests(unittest.TestCase):
    def test_redacts_exact_credentials_but_not_document_token(self) -> None:
        result = sanitize_snapshot(
            {
                "authorization": "Bearer private",
                "nested": {"api_key": "private"},
                "token": {"kind": "text", "text": "kept"},
            },
            max_bytes=INPUT_LIMIT_BYTES,
        )

        self.assertEqual(result["authorization"], "[REDACTED]")
        self.assertEqual(result["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(result["token"], {"kind": "text", "text": "kept"})

    def test_enforces_depth_breadth_string_and_final_size_limits(self) -> None:
        deep = {"value": "end"}
        for _ in range(14):
            deep = {"next": deep}
        bounded = sanitize_snapshot(
            {"deep": deep, "many": list(range(120)), "long": "x" * 5_000},
            max_bytes=INPUT_LIMIT_BYTES,
        )
        self.assertEqual(
            bounded["many"][-1],
            {"_truncated_children": "at_least_one"},
        )
        self.assertTrue(bounded["long"].endswith("…[truncated]"))
        self.assertEqual(len(bounded["long"]), 4_096)
        self.assertIn("maximum_depth", str(bounded["deep"]))

        oversized = sanitize_snapshot(
            {"large": {str(index): "x" * 4_096 for index in range(20)}},
            max_bytes=INPUT_LIMIT_BYTES,
        )
        self.assertTrue(oversized["_mcp_log"]["truncated"])
        self.assertGreater(
            oversized["_mcp_log"]["original_size_bytes"],
            INPUT_LIMIT_BYTES,
        )


class CallLoggingMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def test_logs_success_once_with_command_and_trace(self) -> None:
        middleware = McpCallLoggingMiddleware()
        result = {"content": [{"type": "text", "text": "ok"}], "isError": False}
        call_next = AsyncMock(return_value=result)

        with patch(
            "albayan_mcp.call_logging._trace_id", return_value="f" * 32
        ), patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            returned = await middleware(_context(), call_next)

        self.assertIs(returned, result)
        call_next.assert_awaited_once()
        post.assert_awaited_once()
        event = post.await_args.args[0]
        self.assertEqual(event["tool_name"], "apply_session_command")
        self.assertEqual(event["command_name"], "insert_text_block")
        self.assertEqual(event["trace_id"], "f" * 32)
        self.assertEqual(event["status"], "success")
        self.assertEqual(event["output"], result)

    async def test_classifies_tool_error_result(self) -> None:
        middleware = McpCallLoggingMiddleware()
        result = {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": '{"status":409,"code":"revision_conflict",'
                    '"message":"أعد القراءة","current_revision":4}',
                }
            ],
        }

        with patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            returned = await middleware(_context(), AsyncMock(return_value=result))

        self.assertIs(returned, result)
        event = post.await_args.args[0]
        self.assertEqual(event["status"], "error")
        self.assertIsNone(event["output"])
        self.assertEqual(
            event["error"],
            '{"status":409,"code":"revision_conflict",'
            '"message":"أعد القراءة","current_revision":4}',
        )

    async def test_logs_thrown_error_and_reraises(self) -> None:
        middleware = McpCallLoggingMiddleware()
        failure = BackendApiError(
            status=422,
            code="validation_error",
            message="بيانات الطلب غير صالحة.",
        )

        with patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            with self.assertRaises(BackendApiError):
                await middleware(_context(), AsyncMock(side_effect=failure))

        event = post.await_args.args[0]
        self.assertEqual(event["status"], "error")
        self.assertIsNone(event["output"])
        self.assertIn('"code":"validation_error"', event["error"])

    async def test_non_tool_messages_bypass_logging(self) -> None:
        middleware = McpCallLoggingMiddleware()
        result = {"ok": True}
        call_next = AsyncMock(return_value=result)
        with patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            returned = await middleware(_context(method="tools/list"), call_next)

        self.assertIs(returned, result)
        post.assert_not_awaited()

    async def test_future_command_is_extracted_without_an_operation_registry(self) -> None:
        context = _context(
            params={
                "name": "future_tool",
                "arguments": {"command": {"op": "future_command"}},
            }
        )
        with patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            await McpCallLoggingMiddleware()(context, AsyncMock(return_value={}))

        event = post.await_args.args[0]
        self.assertEqual(event["tool_name"], "future_tool")
        self.assertEqual(event["command_name"], "future_command")

    async def test_malformed_tool_call_is_still_observed_once(self) -> None:
        context = _context(params={"arguments": {}})
        with patch(
            "albayan_mcp.call_logging._post_log", new_callable=AsyncMock
        ) as post:
            await McpCallLoggingMiddleware()(context, AsyncMock(return_value={}))

        post.assert_awaited_once()
        self.assertEqual(post.await_args.args[0]["tool_name"], "<invalid>")

    async def test_logging_transport_failure_is_best_effort(self) -> None:
        with patch(
            "albayan_mcp.call_logging.api_request",
            new_callable=AsyncMock,
            side_effect=RuntimeError("backend unavailable"),
        ):
            await _post_log({"tool_name": "tool"})

    async def test_logging_uses_existing_authenticated_fastapi_client(self) -> None:
        event = {"tool_name": "tool"}
        with patch(
            "albayan_mcp.call_logging.api_request",
            new_callable=AsyncMock,
            return_value=None,
        ) as request:
            await _post_log(event)

        request.assert_awaited_once_with(
            "POST",
            "/api/v1/mcp/call-logs",
            json=event,
            timeout=2.0,
        )


class CallLoggingCompositionTests(unittest.TestCase):
    def test_server_registers_one_call_logging_middleware(self) -> None:
        server = create_server()
        custom = [
            item
            for item in server.middleware
            if isinstance(item, McpCallLoggingMiddleware)
        ]
        self.assertEqual(len(custom), 1)

    def test_logging_module_has_no_private_worker_dependency(self) -> None:
        from albayan_mcp import call_logging

        source = Path(call_logging.__file__).read_text(encoding="utf-8")
        self.assertNotIn("BUTEX_WORKER", source.upper())
        self.assertNotIn("butex_worker_token", source)


if __name__ == "__main__":
    unittest.main()
