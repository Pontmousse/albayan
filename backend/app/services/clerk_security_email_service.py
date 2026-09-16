from __future__ import annotations

from app.services import email_service

SECURITY_TEMPLATE_ALIASES = {
    "account_locked": "account-locked-ar",
    "password_changed": "password-changed-ar",
    "password_removed": "password-removed-ar",
    "primary_email_address_changed": "primary-email-changed-ar",
    "new_device_sign_in": "new-device-sign-in-ar",
}


def _send_security_notice(
    *,
    to: str,
    template_alias: str,
    failure_detail: str,
    idempotency_key: str | None,
) -> str | None:
    return email_service._send_resend_email(
        to=to,
        failure_detail=failure_detail,
        template_alias_or_id=template_alias,
        variables={
            "RECIPIENT_EMAIL": to,
            **email_service._common_variables(),
        },
        idempotency_key=idempotency_key,
    )


def send_account_locked_email(
    *,
    to: str,
    idempotency_key: str | None = None,
) -> str | None:
    return _send_security_notice(
        to=to,
        template_alias=SECURITY_TEMPLATE_ALIASES["account_locked"],
        failure_detail="تعذّر إرسال إشعار قفل الحساب.",
        idempotency_key=idempotency_key,
    )


def send_password_changed_email(
    *,
    to: str,
    idempotency_key: str | None = None,
) -> str | None:
    return _send_security_notice(
        to=to,
        template_alias=SECURITY_TEMPLATE_ALIASES["password_changed"],
        failure_detail="تعذّر إرسال إشعار تغيير كلمة المرور.",
        idempotency_key=idempotency_key,
    )


def send_password_removed_email(
    *,
    to: str,
    idempotency_key: str | None = None,
) -> str | None:
    return _send_security_notice(
        to=to,
        template_alias=SECURITY_TEMPLATE_ALIASES["password_removed"],
        failure_detail="تعذّر إرسال إشعار إزالة كلمة المرور.",
        idempotency_key=idempotency_key,
    )


def send_primary_email_changed_email(
    *,
    to: str,
    idempotency_key: str | None = None,
) -> str | None:
    return _send_security_notice(
        to=to,
        template_alias=SECURITY_TEMPLATE_ALIASES["primary_email_address_changed"],
        failure_detail="تعذّر إرسال إشعار تغيير البريد الأساسي.",
        idempotency_key=idempotency_key,
    )


def send_new_device_sign_in_email(
    *,
    to: str,
    idempotency_key: str | None = None,
) -> str | None:
    return _send_security_notice(
        to=to,
        template_alias=SECURITY_TEMPLATE_ALIASES["new_device_sign_in"],
        failure_detail="تعذّر إرسال إشعار تسجيل الدخول من جهاز جديد.",
        idempotency_key=idempotency_key,
    )
