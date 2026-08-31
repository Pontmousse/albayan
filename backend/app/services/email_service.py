"""إرسال البريد عبر Resend REST API."""

import html as html_lib
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime

from fastapi import HTTPException

from app.core.config import settings
from app.core.dates import format_date_time
from app.models.enums import InvitationRole

_ROLE_LABELS = {
    InvitationRole.REVIEWER: "مراجع",
    InvitationRole.EDITOR: "محرر",
}

logger = logging.getLogger(__name__)


def _send_resend_email(
    *,
    to: str,
    failure_detail: str,
    subject: str | None = None,
    html: str | None = None,
    template_alias_or_id: str | None = None,
    variables: dict[str, str | int] | None = None,
    idempotency_key: str | None = None,
) -> str | None:
    has_template = template_alias_or_id is not None
    has_raw_content = subject is not None or html is not None

    if has_template and has_raw_content:
        raise ValueError("لا يمكن الجمع بين قالب البريد ومحتوى subject/html.")
    if not has_template and not has_raw_content:
        raise ValueError("يلزم تحديد قالب بريد أو subject/html لإرسال البريد.")
    if has_raw_content and (subject is None or html is None):
        raise ValueError("يلزم تحديد subject وhtml معاً لإرسال محتوى خام.")

    api_key = (
        settings.resend_api_key.get_secret_value()
        if hasattr(settings.resend_api_key, "get_secret_value")
        else settings.resend_api_key
    )
    if not api_key or not settings.email_from or not settings.email_reply_to:
        raise HTTPException(
            status_code=503,
            detail="خدمة البريد غير مُهيّأة على الخادم.",
        )

    payload_dict: dict[str, object] = {
        "from": settings.email_from,
        "reply_to": settings.email_reply_to,
        "to": [to],
    }
    if has_template:
        payload_dict["template"] = {
            "id": template_alias_or_id,
            "variables": variables or {},
        }
    else:
        payload_dict["subject"] = subject
        payload_dict["html"] = html

    payload = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=failure_detail,
                )
            body = resp.read() if callable(getattr(resp, "read", None)) else b""
            if not isinstance(body, bytes) or not body:
                return None
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                return None
            message_id = data.get("id") if isinstance(data, dict) else None
            if isinstance(message_id, str):
                logger.info("Resend accepted email to %s with id %s", to, message_id)
                return message_id
            return None
    except HTTPException:
        raise
    except urllib.error.HTTPError as exc:
        logger.warning("Resend rejected email to %s with status %s", to, exc.code)
        raise HTTPException(
            status_code=502,
            detail=failure_detail,
        ) from exc
    except Exception as exc:
        logger.warning("Resend email failed for %s (%s)", to, type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=failure_detail,
        ) from exc


def send_welcome_email(*, to: str, user_name: str | None) -> None:
    if not settings.resend_welcome_template:
        raise HTTPException(
            status_code=503,
            detail="قالب بريد الترحيب غير مُهيّأ على الخادم.",
        )

    site_url = settings.frontend_base_url.rstrip("/")
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد الترحيب.",
        template_alias_or_id=settings.resend_welcome_template,
        variables={
            "USER_NAME": user_name or "الباحث الكريم",
            "LOGIN_URL": f"{site_url}/maktabi",
            "SITE_URL": site_url,
            "CONTACT_EMAIL": settings.email_reply_to_address,
            "ASSET_BASE_URL": settings.email_asset_base_url.rstrip("/"),
        },
    )


def send_app_invitation_email(
    *,
    to: str,
    invitation_url: str,
    expires_text: str | None,
) -> None:
    if not settings.resend_app_invitation_template:
        raise HTTPException(
            status_code=503,
            detail="قالب بريد دعوة المستخدم غير مُهيّأ على الخادم.",
        )

    site_url = settings.frontend_base_url.rstrip("/")
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال دعوة المستخدم.",
        template_alias_or_id=settings.resend_app_invitation_template,
        variables={
            "INVITATION_URL": invitation_url,
            "RECIPIENT_EMAIL": to,
            "EXPIRES_TEXT": expires_text or "",
            "SITE_URL": site_url,
            "CONTACT_EMAIL": settings.email_reply_to_address,
            "ASSET_BASE_URL": settings.email_asset_base_url.rstrip("/"),
        },
    )


def send_auth_verification_email(
    *,
    to: str,
    otp_code: str,
    idempotency_key: str | None = None,
) -> str | None:
    if not settings.resend_auth_verification_template:
        raise HTTPException(
            status_code=503,
            detail="قالب بريد تحقق الحساب غير مُهيّأ على الخادم.",
        )

    site_url = settings.frontend_base_url.rstrip("/")
    return _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رمز تحقق الحساب.",
        template_alias_or_id=settings.resend_auth_verification_template,
        variables={
            "OTP_CODE": otp_code,
            "RECIPIENT_EMAIL": to,
            "SITE_URL": site_url,
            "CONTACT_EMAIL": settings.email_reply_to_address,
            "ASSET_BASE_URL": settings.email_asset_base_url.rstrip("/"),
        },
        idempotency_key=idempotency_key,
    )


def send_password_reset_email(
    *,
    to: str,
    otp_code: str,
    idempotency_key: str | None = None,
) -> str | None:
    if not settings.resend_password_reset_template:
        raise HTTPException(
            status_code=503,
            detail="قالب بريد استعادة كلمة المرور غير مُهيّأ على الخادم.",
        )

    site_url = settings.frontend_base_url.rstrip("/")
    return _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رمز استعادة كلمة المرور.",
        template_alias_or_id=settings.resend_password_reset_template,
        variables={
            "OTP_CODE": otp_code,
            "RECIPIENT_EMAIL": to,
            "SITE_URL": site_url,
            "CONTACT_EMAIL": settings.email_reply_to_address,
            "ASSET_BASE_URL": settings.email_asset_base_url.rstrip("/"),
        },
        idempotency_key=idempotency_key,
    )


def send_invitation_email(
    *,
    to: str,
    article_title: str,
    role: InvitationRole,
    token: str,
    expires_at: datetime,
) -> None:
    role_label = _ROLE_LABELS.get(role, role.value)
    link = f"{settings.frontend_base_url.rstrip('/')}/daawa/{token}"
    expires_text = format_date_time(expires_at)
    article_title_safe = html_lib.escape(article_title)
    role_label_safe = html_lib.escape(role_label)
    link_safe = html_lib.escape(link, quote=True)

    subject = f"دعوة للمشاركة في مقال «{article_title}» — مجلة البيان"
    html = f"""
    <div dir="rtl" style="font-family: sans-serif; line-height: 1.7;">
      <p>السلام عليكم،</p>
      <p>
        دُعيت للمشاركة في مقال <strong>{article_title_safe}</strong>
        بدور <strong>{role_label_safe}</strong> في مجلة البيان.
      </p>
      <p>
        <a href="{link_safe}">اضغط هنا لقبول الدعوة</a>
      </p>
      <p>تنتهي صلاحية الدعوة في: {expires_text}</p>
      <p>إن لم تتوقع هذه الرسالة يمكنك تجاهلها.</p>
    </div>
    """

    _send_resend_email(
        to=to,
        subject=subject,
        html=html,
        failure_detail="تعذّر إرسال بريد الدعوة، حاول مجدداً.",
    )
