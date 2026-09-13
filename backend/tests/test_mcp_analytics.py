from __future__ import annotations

import importlib.util
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError

from app.core.actor import Actor
from app.core.clerk import AuthContext
from app.document2_registry import (
    DOCUMENT2_COMMAND_GROUP_BY_NAME,
    DOCUMENT2_COMMAND_GROUPS,
)
from app.models.base import Base
from app.models.mcp_call_log import McpCallLog
from app.models.user import User
from app.routers import admin_mcp, mcp_logs
from app.schemas.document2 import DocumentCommand
from app.schemas.mcp_analytics import McpCallLogCreate
from app.services import mcp_analytics_service


def _result(*, one=None, rows=None):
    result = MagicMock()
    result.one.return_value = one
    result.all.return_value = rows or []
    return result


def _payload(**overrides) -> McpCallLogCreate:
    values = {
        "trace_id": "1" * 32,
        "tool_name": "apply_session_command",
        "command_name": "insert_text_block",
        "status": "success",
        "duration_ms": 12,
        "input": {"article_id": "article_1"},
        "output": {"revision": 2},
        "error": None,
    }
    values.update(overrides)
    return McpCallLogCreate.model_validate(values)


class McpCallLogSchemaTests(unittest.TestCase):
    def test_sanitizes_credentials_but_preserves_document_token(self) -> None:
        payload = _payload(
            input={
                "authorization": "Bearer private",
                "nested": {"api_key": "private", "token": {"kind": "text"}},
            }
        )

        self.assertEqual(payload.input["authorization"], "[REDACTED]")
        self.assertEqual(payload.input["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(payload.input["nested"]["token"], {"kind": "text"})

    def test_bounds_snapshots_depth_collections_strings_and_final_bytes(self) -> None:
        nested: dict[str, object] = {"value": "end"}
        for _ in range(14):
            nested = {"next": nested}
        payload = _payload(
            input={
                "deep": nested,
                "many": list(range(120)),
                "long": "x" * 5_000,
                "oversized": {str(index): "y" * 4_096 for index in range(20)},
            }
        )

        self.assertTrue(payload.input["_mcp_log"]["truncated"])
        self.assertEqual(payload.input["_mcp_log"]["limit_bytes"], 32 * 1024)

    def test_sanitizes_bearer_in_error_and_enforces_result_shape(self) -> None:
        payload = _payload(
            status="error",
            output=None,
            error="failed with Bearer abc.def.ghi",
        )
        self.assertEqual(payload.error, "failed with Bearer [REDACTED]")

        invalid = [
            {"status": "success", "output": None},
            {"status": "error", "output": None, "error": None},
            {"status": "success", "duration_ms": "12"},
            {"status": "success", "output": {}, "unknown": True},
            {"status": "success", "output": {}, "input": []},
            {"status": "success", "output": {}, "trace_id": "ABC"},
        ]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                values = _payload().model_dump()
                values.update(changes)
                McpCallLogCreate.model_validate(values)


class McpRegistryAndModelTests(unittest.TestCase):
    def test_taxonomy_exactly_covers_authoritative_command_union(self) -> None:
        schema = TypeAdapter(DocumentCommand).json_schema()
        operations = set(schema["discriminator"]["mapping"])

        self.assertEqual(len(operations), 29)
        self.assertEqual(set(DOCUMENT2_COMMAND_GROUP_BY_NAME), operations)
        grouped = [name for _, commands in DOCUMENT2_COMMAND_GROUPS for name in commands]
        self.assertEqual(len(grouped), len(set(grouped)))

    def test_model_metadata_has_constraints_and_requested_indexes(self) -> None:
        table = Base.metadata.tables["mcp_call_logs"]
        self.assertIs(table, McpCallLog.__table__)
        self.assertEqual(
            {index.name for index in table.indexes},
            {
                "ix_mcp_call_logs_created_at",
                "ix_mcp_call_logs_tool_created_at",
                "ix_mcp_call_logs_command_created_at",
                "ix_mcp_call_logs_status_created_at",
                "ix_mcp_call_logs_user_created_at",
            },
        )
        constraints = {constraint.name for constraint in table.constraints}
        self.assertIn("ck_mcp_call_logs_status", constraints)
        self.assertIn("ck_mcp_call_logs_duration_nonnegative", constraints)

    def test_migration_upgrade_and_downgrade_cover_table_and_indexes(self) -> None:
        path = Path(__file__).parents[1] / "alembic/versions/014_add_mcp_call_logs.py"
        spec = importlib.util.spec_from_file_location("migration_014", path)
        assert spec and spec.loader
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        fake_op = MagicMock()

        with patch.object(migration, "op", fake_op):
            migration.upgrade()
            migration.downgrade()

        self.assertEqual(fake_op.create_table.call_args.args[0], "mcp_call_logs")
        self.assertEqual(fake_op.create_index.call_count, 5)
        self.assertEqual(fake_op.drop_index.call_count, 5)
        fake_op.drop_table.assert_called_once_with("mcp_call_logs")


class McpIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.agent = Actor(
            user_id=self.user_id,
            clerk_id="agent",
            auth_method="agent",
        )

    def test_agent_ingestion_uses_server_owned_identity(self) -> None:
        payload = _payload()
        with patch.object(mcp_logs.settings, "mcp_enabled", True), patch.object(
            mcp_logs.mcp_analytics_service, "create_call_log"
        ) as create:
            response = mcp_logs.create_mcp_call_log(payload, self.agent, self.db)

        self.assertEqual(response.status_code, 204)
        create.assert_called_once_with(
            self.db,
            user_id=self.user_id,
            payload=payload,
        )

    def test_ingestion_rejects_humans_and_disabled_feature(self) -> None:
        human = Actor(
            user_id=self.user_id,
            clerk_id="human",
            auth_method="human",
        )
        with patch.object(mcp_logs.settings, "mcp_enabled", True):
            with self.assertRaises(HTTPException) as human_error:
                mcp_logs.create_mcp_call_log(_payload(), human, self.db)
        self.assertEqual(human_error.exception.status_code, 403)

        with patch.object(mcp_logs.settings, "mcp_enabled", False):
            with self.assertRaises(HTTPException) as disabled_error:
                mcp_logs.create_mcp_call_log(_payload(), self.agent, self.db)
        self.assertEqual(disabled_error.exception.status_code, 404)

    def test_service_supplies_database_id_and_timestamp(self) -> None:
        payload = _payload()
        row = mcp_analytics_service.create_call_log(
            self.db,
            user_id=self.user_id,
            payload=payload,
        )

        self.assertIsNone(row.id)
        self.assertIsNone(row.created_at)
        self.assertEqual(row.user_id, self.user_id)
        self.db.add.assert_called_once_with(row)
        self.db.commit.assert_called_once_with()
        self.db.refresh.assert_called_once_with(row)


class McpAnalyticsServiceTests(unittest.TestCase):
    def test_aggregates_comparison_buckets_and_all_known_commands(self) -> None:
        db = MagicMock()
        now = datetime(2026, 9, 13, 12, 30, tzinfo=UTC)
        db.execute.side_effect = [
            _result(one=(10, 8, 25.4, 6, 3)),
            _result(rows=[("apply_session_command", 6, 5, 30.2)]),
            _result(
                rows=[
                    ("insert_text_block", 5, 4),
                    ("future_command", 1, 1),
                ]
            ),
            _result(rows=[(datetime(2026, 9, 13, tzinfo=UTC), 2, 1)]),
        ]
        db.scalar.return_value = 5

        result = mcp_analytics_service.analytics(db, "7d", now=now)

        self.assertEqual(result.summary.total_calls, 10)
        self.assertEqual(result.summary.failed_calls, 2)
        self.assertEqual(result.summary.success_rate, 80.0)
        self.assertEqual(result.summary.average_duration_ms, 25)
        self.assertEqual(result.summary.previous_period_change_percent, 100.0)
        self.assertEqual(result.tools[0].share_percent, 60.0)
        self.assertGreaterEqual(len(result.timeline), 7)
        known = {
            command.command_name
            for group in result.command_groups
            if group.key != "other"
            for command in group.commands
        }
        self.assertEqual(known, set(DOCUMENT2_COMMAND_GROUP_BY_NAME))
        other = next(group for group in result.command_groups if group.key == "other")
        self.assertEqual(other.commands[0].command_name, "future_command")

    def test_empty_analytics_is_stable_and_90d_has_no_comparison(self) -> None:
        db = MagicMock()
        db.execute.side_effect = [
            _result(one=(0, None, None, 0, 0)),
            _result(rows=[]),
            _result(rows=[]),
            _result(rows=[]),
        ]

        result = mcp_analytics_service.analytics(
            db,
            "90d",
            now=datetime(2026, 9, 13, tzinfo=UTC),
        )

        self.assertEqual(result.summary.success_rate, 0)
        self.assertIsNone(result.summary.previous_period_change_percent)
        self.assertEqual(len(result.command_groups), 6)
        db.scalar.assert_not_called()

    def test_cursor_pagination_and_filters(self) -> None:
        now = datetime(2026, 9, 13, tzinfo=UTC)
        rows = []
        for offset in range(3):
            row = McpCallLog(
                id=uuid.uuid4(),
                created_at=now - timedelta(minutes=offset),
                user_id=None,
                tool_name="tool",
                command_name=None,
                status="success",
                duration_ms=offset,
                input_json={},
                output_json={},
            )
            rows.append((row, None))
        db = MagicMock()
        db.execute.return_value.all.return_value = rows

        result = mcp_analytics_service.list_calls(
            db,
            period="24h",
            tool_name="tool",
            status="success",
            limit=2,
            now=now,
        )

        self.assertEqual(len(result.items), 2)
        self.assertIsNotNone(result.next_cursor)
        decoded_time, decoded_id = mcp_analytics_service._decode_cursor(
            result.next_cursor or ""
        )
        self.assertEqual(decoded_time, rows[1][0].created_at)
        self.assertEqual(decoded_id, rows[1][0].id)

        with self.assertRaises(HTTPException) as error:
            mcp_analytics_service._decode_cursor("not-a-cursor")
        self.assertEqual(error.exception.status_code, 422)

    def test_detail_and_retention(self) -> None:
        call_id = uuid.uuid4()
        row = McpCallLog(
            id=call_id,
            created_at=datetime(2026, 9, 13, tzinfo=UTC),
            tool_name="tool",
            command_name=None,
            status="error",
            duration_ms=10,
            input_json={"a": 1},
            output_json=None,
            error="failed",
        )
        db = MagicMock()
        db.execute.return_value.one_or_none.return_value = (row, None)
        detail = mcp_analytics_service.get_call(
            db,
            call_id,
            now=datetime(2026, 9, 13, tzinfo=UTC),
        )
        self.assertEqual(detail.input, {"a": 1})

        db.execute.return_value.one_or_none.return_value = None
        with self.assertRaises(HTTPException) as old_or_missing:
            mcp_analytics_service.get_call(
                db,
                uuid.uuid4(),
                now=datetime(2026, 9, 13, tzinfo=UTC),
            )
        self.assertEqual(old_or_missing.exception.status_code, 404)

        deletion = MagicMock(rowcount=4)
        db.execute.return_value = deletion
        deleted = mcp_analytics_service.delete_expired_logs(
            db,
            now=datetime(2026, 9, 13, tzinfo=UTC),
        )
        self.assertEqual(deleted, 4)
        db.commit.assert_called_once_with()


class McpAdminBoundaryTests(unittest.TestCase):
    def test_admin_analytics_is_feature_gated(self) -> None:
        auth = AuthContext(clerk_id="admin", email="admin@example.com", full_name=None)
        db = MagicMock()
        with patch.object(admin_mcp.settings, "mcp_enabled", False):
            with self.assertRaises(HTTPException) as error:
                admin_mcp.get_mcp_analytics(auth, db, "7d")
        self.assertEqual(error.exception.status_code, 404)

    def test_admin_analytics_delegates_after_admin_resolution(self) -> None:
        auth = AuthContext(clerk_id="admin", email="admin@example.com", full_name=None)
        user = User(
            id=uuid.uuid4(),
            clerk_id="admin",
            email="admin@example.com",
            full_name="Admin",
            is_admin=True,
        )
        expected = MagicMock()
        db = MagicMock()
        with patch.object(admin_mcp.settings, "mcp_enabled", True), patch.object(
            admin_mcp, "current_user", return_value=user
        ), patch.object(
            admin_mcp.mcp_analytics_service, "analytics", return_value=expected
        ) as analytics:
            result = admin_mcp.get_mcp_analytics(auth, db, "30d")

        self.assertIs(result, expected)
        analytics.assert_called_once_with(db, "30d")


if __name__ == "__main__":
    unittest.main()
