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
    variables: dict[str, str] | None = None,
    reply_to: str | None = None,
) -> None:
    has_template = template_alias_or_id is not None
    has_raw_content = subject is not None or html is not None

    if has_template and has_raw_content:
        raise ValueError("لا يمكن الجمع بين قالب البريد ومحتوى subject/html.")
    if not has_template and not has_raw_content:
        raise ValueError("يلزم تحديد قالب بريد أو subject/html لإرسال البريد.")
    if has_raw_content and (subject is None or html is None):
        raise ValueError("يلزم تحديد subject وhtml معاً لإرسال محتوى خام.")

    if not settings.resend_api_key or not settings.email_from:
        raise HTTPException(
            status_code=503,
            detail="خدمة البريد غير مُهيّأة على الخادم.",
        )

    if has_template:
        payload_dict: dict[str, object] = {
            "from": settings.email_from,
            "to": [to],
            "template": {
                "id": template_alias_or_id,
                "variables": variables or {},
            },
        }
    else:
        payload_dict = {
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }

    if reply_to is not None:
        payload_dict["reply_to"] = reply_to

    payload = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=failure_detail,
                )
    except HTTPException:
        raise
    except urllib.error.HTTPError as exc:
        logger.warning("Resend rejected email to %s with status %s", to, exc.code)
        raise HTTPException(
            status_code=502,
            detail=failure_detail,
        ) from exc
    except Exception as exc:
        logger.warning("Resend email failed for %s: %s", to, exc)
        raise HTTPException(
            status_code=502,
            detail=failure_detail,
        ) from exc


def send_welcome_email(*, to: str, user_name: str | None) -> None:
    if not settings.resend_welcome_template_id:
        raise HTTPException(
            status_code=503,
            detail="قالب بريد الترحيب غير مُهيّأ على الخادم.",
        )

    site_url = settings.frontend_base_url.rstrip("/")
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد الترحيب.",
        template_alias_or_id=settings.resend_welcome_template_id,
        variables={
            "USER_NAME": user_name or "الباحث الكريم",
            "LOGIN_URL": f"{site_url}/maktabi",
            "SITE_URL": site_url,
            "ASSET_BASE_URL": settings.email_asset_base_url.rstrip("/"),
        },
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
