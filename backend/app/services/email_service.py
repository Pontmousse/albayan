"""إرسال بريد الدعوات عبر Resend REST API."""

import json
import urllib.error
import urllib.request
from datetime import datetime

from fastapi import HTTPException

from app.core.config import settings
from app.models.enums import InvitationRole

_ROLE_LABELS = {
    InvitationRole.REVIEWER: "مراجع",
    InvitationRole.EDITOR: "محرر",
}


def send_invitation_email(
    *,
    to: str,
    article_title: str,
    role: InvitationRole,
    token: str,
    expires_at: datetime,
) -> None:
    if not settings.resend_api_key or not settings.email_from:
        raise HTTPException(
            status_code=503,
            detail="خدمة البريد غير مُهيّأة على الخادم.",
        )

    role_label = _ROLE_LABELS.get(role, role.value)
    link = f"{settings.frontend_base_url.rstrip('/')}/daawa/{token}"
    expires_text = expires_at.strftime("%Y-%m-%d %H:%M UTC")

    subject = f"دعوة للمشاركة في مقال «{article_title}» — مجلة البيان"
    html = f"""
    <div dir="rtl" style="font-family: sans-serif; line-height: 1.7;">
      <p>السلام عليكم،</p>
      <p>
        دُعيت للمشاركة في مقال <strong>{article_title}</strong>
        بدور <strong>{role_label}</strong> في مجلة البيان.
      </p>
      <p>
        <a href="{link}">اضغط هنا لقبول الدعوة</a>
      </p>
      <p>تنتهي صلاحية الدعوة في: {expires_text}</p>
      <p>إن لم تتوقع هذه الرسالة يمكنك تجاهلها.</p>
    </div>
    """

    payload = json.dumps(
        {
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }
    ).encode("utf-8")

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
                    detail="تعذّر إرسال بريد الدعوة، حاول مجدداً.",
                )
    except HTTPException:
        raise
    except urllib.error.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="تعذّر إرسال بريد الدعوة، حاول مجدداً.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="تعذّر إرسال بريد الدعوة، حاول مجدداً.",
        ) from exc
