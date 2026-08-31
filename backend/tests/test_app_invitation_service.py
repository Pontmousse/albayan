import inspect
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from clerk_backend_api import models
from fastapi import HTTPException

from app.core.clerk import AuthContext
from app.routers import admin
from app.services import app_invitation_service


def _clerk_invitation(**overrides):
    values = {
        "id": "inv_test",
        "email_address": "person@example.com",
        "status": "pending",
        "url": "https://accounts.example/invitations/accept?__clerk_ticket=ticket",
        "created_at": 1_785_542_400,
        "updated_at": 1_785_542_500,
        "expires_at": 1_788_192_000,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _clerk_error(status_code: int, code: str) -> models.ClerkErrors:
    response = httpx.Response(
        status_code,
        json={"errors": [{"code": code, "message": "provider", "long_message": "provider"}]},
        request=httpx.Request("POST", "https://api.clerk.com/v1/invitations"),
    )
    return models.ClerkErrors(
        models.ClerkErrorsData(
            errors=[
                models.ClerkError(
                    code=code,
                    message="provider",
                    long_message="provider",
                )
            ]
        ),
        response,
    )


class AppInvitationServiceTests(unittest.TestCase):
    def test_admin_invitation_endpoints_use_admin_dependency(self) -> None:
        self.assertEqual(
            inspect.signature(admin.create_app_invitation).parameters["auth"].annotation,
            admin.AdminDep,
        )
        self.assertEqual(
            inspect.signature(admin.list_app_invitations).parameters["auth"].annotation,
            admin.AdminDep,
        )
        self.assertEqual(
            inspect.signature(admin.revoke_app_invitation).parameters["auth"].annotation,
            admin.AdminDep,
        )

    def test_create_uses_clerk_invitation_url_and_disables_clerk_email(self) -> None:
        admin_auth = AuthContext(
            clerk_id="user_admin",
            email="admin@example.com",
            full_name="المدير",
        )
        returned = _clerk_invitation()

        with patch.object(
            app_invitation_service.settings,
            "frontend_base_url",
            "https://albayan-journal.org/",
        ), patch.object(
            app_invitation_service.clerk_client.invitations,
            "create",
            return_value=returned,
        ) as create, patch.object(
            app_invitation_service,
            "format_date",
            return_value="١٥ ربيع الأول ١٤٤٨ هـ",
        ), patch.object(
            app_invitation_service,
            "send_app_invitation_email",
        ) as send_email:
            invitation = app_invitation_service.create_app_invitation(
                email=" Person@Example.COM ",
                admin=admin_auth,
            )

        create.assert_called_once_with(
            request={
                "email_address": "person@example.com",
                "redirect_url": "https://albayan-journal.org/tasjil",
                "notify": False,
                "ignore_existing": False,
                "public_metadata": {
                    "source": "albayan-admin",
                    "invited_by_clerk_id": "user_admin",
                },
            }
        )
        send_email.assert_called_once_with(
            to="person@example.com",
            invitation_url=returned.url,
            expires_text="١٥ ربيع الأول ١٤٤٨ هـ",
        )
        self.assertEqual(invitation.id, "inv_test")
        self.assertEqual(invitation.status, "pending")

    def test_duplicate_invitation_or_user_maps_to_conflict(self) -> None:
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "create",
            side_effect=_clerk_error(422, "form_identifier_exists"),
        ):
            with self.assertRaises(HTTPException) as raised:
                app_invitation_service.create_app_invitation(
                    email="person@example.com",
                    admin=AuthContext("user_admin", "admin@example.com", None),
                )

        self.assertEqual(raised.exception.status_code, 409)

    def test_list_returns_compact_clerk_invitations(self) -> None:
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "list",
            return_value=[_clerk_invitation(id="inv_1")],
        ) as list_invitations:
            rows = app_invitation_service.list_app_invitations()

        list_invitations.assert_called_once_with(limit=50, order_by="-created_at")
        self.assertEqual(rows[0].id, "inv_1")
        self.assertEqual(rows[0].created_at, datetime(2026, 8, 1, tzinfo=UTC))

    def test_revoke_calls_clerk(self) -> None:
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "revoke",
            return_value=Mock(),
        ) as revoke:
            app_invitation_service.revoke_app_invitation("inv_test")

        revoke.assert_called_once_with(invitation_id="inv_test")


if __name__ == "__main__":
    unittest.main()
