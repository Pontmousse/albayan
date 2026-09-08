import inspect
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from clerk_backend_api import models
from fastapi import HTTPException

from app.core.clerk import AuthContext
from app.models.enums import UserGender
from app.routers import admin, public
from app.services import app_invitation_service


def _clerk_invitation(**overrides):
    values = {
        "id": "inv_test",
        "email_address": "person@example.com",
        "status": "pending",
        "url": "https://clerk.albayan-journal.org/v1/tickets/accept?ticket=secret-ticket",
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
        self.assertEqual(
            inspect.signature(admin.resend_app_invitation).parameters["auth"].annotation,
            admin.AdminDep,
        )

    def test_handoff_continuation_route_is_post_only(self) -> None:
        route = next(
            route
            for route in public.router.routes
            if getattr(route, "path", "") == "/api/v1/public/app-invitations/{token}/continue"
        )
        self.assertEqual(route.methods, {"POST"})

    def test_create_emails_first_party_handoff_and_disables_clerk_email(self) -> None:
        admin_auth = AuthContext(
            clerk_id="user_admin",
            email="admin@example.com",
            full_name="المدير",
        )
        returned = _clerk_invitation()
        handoff_url = "https://albayan-journal.org/tasjil/invitation/signed-token"

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
            "_handoff_url",
            return_value=handoff_url,
        ), patch.object(
            app_invitation_service,
            "send_app_invitation_email",
        ) as send_email:
            invitation = app_invitation_service.create_app_invitation(
                email=" Person@Example.COM ",
                full_name="  أحمد   الزهراني  ",
                gender=UserGender.MALE,
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
                    "albayan_invitee_name": "أحمد الزهراني",
                    "albayan_gender": "male",
                },
            }
        )
        send_email.assert_called_once_with(
            to="person@example.com",
            recipient_name="أحمد الزهراني",
            invitation_url=handoff_url,
            expires_text="١٥ ربيع الأول ١٤٤٨ هـ",
            idempotency_key="app-invitation/inv_test",
        )
        self.assertNotIn("clerk.albayan-journal.org", send_email.call_args.kwargs["invitation_url"])
        self.assertNotIn("ticket=", send_email.call_args.kwargs["invitation_url"])
        self.assertEqual(invitation.id, "inv_test")
        self.assertEqual(invitation.status, "pending")
        self.assertEqual(invitation.full_name, "أحمد الزهراني")
        self.assertEqual(invitation.gender, UserGender.MALE)

    def test_duplicate_invitation_or_user_maps_to_conflict(self) -> None:
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "create",
            side_effect=_clerk_error(422, "form_identifier_exists"),
        ):
            with self.assertRaises(HTTPException) as raised:
                app_invitation_service.create_app_invitation(
                    email="person@example.com",
                    full_name="سلمى الباحثة",
                    gender=UserGender.FEMALE,
                    admin=AuthContext("user_admin", "admin@example.com", None),
                )

        self.assertEqual(raised.exception.status_code, 409)

    def test_failed_resend_delivery_revokes_new_clerk_invitation(self) -> None:
        returned = _clerk_invitation()
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "create",
            return_value=returned,
        ), patch.object(
            app_invitation_service.clerk_client.invitations,
            "revoke",
        ) as revoke, patch.object(
            app_invitation_service,
            "_handoff_url",
            return_value="https://albayan-journal.org/tasjil/invitation/signed-token",
        ), patch.object(
            app_invitation_service,
            "send_app_invitation_email",
            side_effect=HTTPException(status_code=502, detail="mail failed"),
        ):
            with self.assertRaises(HTTPException):
                app_invitation_service.create_app_invitation(
                    email="person@example.com",
                    full_name="سلمى الباحثة",
                    gender=UserGender.FEMALE,
                    admin=AuthContext("user_admin", "admin@example.com", None),
                )

        revoke.assert_called_once_with(invitation_id="inv_test")

    def test_resend_pending_app_invitation_uses_handoff_url(self) -> None:
        returned = _clerk_invitation()
        handoff_url = "https://albayan-journal.org/tasjil/invitation/resend-token"
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "list",
            return_value=[returned],
        ), patch.object(
            app_invitation_service,
            "_handoff_url",
            return_value=handoff_url,
        ), patch.object(
            app_invitation_service,
            "send_app_invitation_email",
        ) as send:
            invitation = app_invitation_service.resend_app_invitation("inv_test")

        self.assertEqual(invitation.id, "inv_test")
        send.assert_called_once_with(
            to="person@example.com",
            recipient_name=None,
            invitation_url=handoff_url,
            expires_text=app_invitation_service.format_date(invitation.expires_at),
        )
        self.assertNotEqual(send.call_args.kwargs["invitation_url"], returned.url)

    def test_user_continuation_resolves_clerk_url_server_side(self) -> None:
        returned = _clerk_invitation()
        claims = SimpleNamespace(subject="inv_test")
        with patch.object(
            app_invitation_service,
            "verify_handoff_token",
            return_value=claims,
        ), patch.object(
            app_invitation_service.clerk_client.invitations,
            "list",
            return_value=[returned],
        ):
            destination = app_invitation_service.continue_app_invitation_handoff(
                "signed-token"
            )

        self.assertEqual(destination, returned.url)

    def test_non_pending_handoff_fails_without_returning_clerk_url(self) -> None:
        returned = _clerk_invitation(status="accepted")
        claims = SimpleNamespace(subject="inv_test")
        with patch.object(
            app_invitation_service,
            "verify_handoff_token",
            return_value=claims,
        ), patch.object(
            app_invitation_service.clerk_client.invitations,
            "list",
            return_value=[returned],
        ):
            with self.assertRaises(HTTPException) as raised:
                app_invitation_service.continue_app_invitation_handoff("signed-token")

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

    def test_list_reads_name_and_gender_from_invitation_metadata(self) -> None:
        returned = _clerk_invitation(
            public_metadata={
                "albayan_invitee_name": "ليلى العامرية",
                "albayan_gender": "female",
            }
        )
        with patch.object(
            app_invitation_service.clerk_client.invitations,
            "list",
            return_value=[returned],
        ):
            invitation = app_invitation_service.list_app_invitations()[0]

        self.assertEqual(invitation.full_name, "ليلى العامرية")
        self.assertEqual(invitation.gender, UserGender.FEMALE)

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
