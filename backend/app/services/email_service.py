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


def _site_url() -> str:
    return settings.frontend_base_url.rstrip("/")


def _asset_base_url() -> str:
    return settings.email_asset_base_url.rstrip("/")


def _contact_email() -> str:
    return settings.email_reply_to_address


def _common_variables() -> dict[str, str]:
    return {
        "SITE_URL": _site_url(),
        "CONTACT_EMAIL": _contact_email(),
        "ASSET_BASE_URL": _asset_base_url(),
    }


def _require_template(value: str, detail: str) -> str:
    if not value:
        raise HTTPException(status_code=503, detail=detail)
    return value


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
    template = _require_template(
        settings.resend_welcome_template,
        "قالب بريد الترحيب غير مُهيّأ على الخادم.",
    )

    site_url = _site_url()
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد الترحيب.",
        template_alias_or_id=template,
        variables={
            "USER_NAME": user_name or "الباحث الكريم",
            "LOGIN_URL": f"{site_url}/maktabi",
            **_common_variables(),
        },
    )


def send_app_invitation_email(
    *,
    to: str,
    invitation_url: str,
    expires_text: str | None,
) -> None:
    template = _require_template(
        settings.resend_app_invitation_template,
        "قالب بريد دعوة المستخدم غير مُهيّأ على الخادم.",
    )

    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال دعوة المستخدم.",
        template_alias_or_id=template,
        variables={
            "INVITATION_URL": invitation_url,
            "RECIPIENT_EMAIL": to,
            "EXPIRES_TEXT": expires_text or "",
            **_common_variables(),
        },
    )


def send_auth_verification_email(
    *,
    to: str,
    otp_code: str,
    idempotency_key: str | None = None,
) -> str | None:
    template = _require_template(
        settings.resend_auth_verification_template,
        "قالب بريد تحقق الحساب غير مُهيّأ على الخادم.",
    )

    return _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رمز تحقق الحساب.",
        template_alias_or_id=template,
        variables={
            "OTP_CODE": otp_code,
            "RECIPIENT_EMAIL": to,
            **_common_variables(),
        },
        idempotency_key=idempotency_key,
    )


def send_password_reset_email(
    *,
    to: str,
    otp_code: str,
    idempotency_key: str | None = None,
) -> str | None:
    template = _require_template(
        settings.resend_password_reset_template,
        "قالب بريد استعادة كلمة المرور غير مُهيّأ على الخادم.",
    )

    return _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رمز استعادة كلمة المرور.",
        template_alias_or_id=template,
        variables={
            "OTP_CODE": otp_code,
            "RECIPIENT_EMAIL": to,
            **_common_variables(),
        },
        idempotency_key=idempotency_key,
    )


def send_submission_received_email(
    *,
    to: str,
    article_title: str,
    article_url: str,
    submitted_text: str,
    version_number: int,
) -> None:
    template = _require_template(
        settings.resend_submission_received_template,
        "قالب بريد استلام البحث غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال تأكيد استلام البحث.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "ARTICLE_URL": article_url,
            "SUBMITTED_TEXT": submitted_text,
            "VERSION_NUMBER": version_number,
            **_common_variables(),
        },
        idempotency_key=f"submission-received/{article_url.rsplit('/', 1)[-1]}/{version_number}",
    )


def send_new_submission_alert_email(
    *,
    to: str,
    article_title: str,
    author_name: str,
    article_url: str,
) -> None:
    template = _require_template(
        settings.resend_new_submission_alert_template,
        "قالب بريد تنبيه البحث الجديد غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال تنبيه البحث الجديد.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "AUTHOR_NAME": author_name,
            "ARTICLE_URL": article_url,
            **_common_variables(),
        },
    )


def send_editor_assigned_email(*, to: str, article_title: str, article_url: str) -> None:
    template = _require_template(
        settings.resend_editor_assigned_template,
        "قالب بريد تعيين المحرر غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد تعيين المحرر.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "ARTICLE_URL": article_url,
            **_common_variables(),
        },
    )


def send_reviewer_assigned_email(
    *, to: str, article_title: str, review_url: str, due_text: str
) -> None:
    template = _require_template(
        settings.resend_reviewer_assigned_template,
        "قالب بريد تعيين المراجع غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد تعيين المراجع.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "REVIEW_URL": review_url,
            "DUE_TEXT": due_text,
            **_common_variables(),
        },
    )


def send_review_reminder_email(
    *,
    to: str,
    article_title: str,
    review_url: str,
    due_text: str,
    reminder_text: str,
    idempotency_key: str,
) -> None:
    template = _require_template(
        settings.resend_review_reminder_template,
        "قالب بريد تذكير المراجع غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال تذكير المراجعة.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "REVIEW_URL": review_url,
            "DUE_TEXT": due_text,
            "REMINDER_TEXT": reminder_text,
            **_common_variables(),
        },
        idempotency_key=idempotency_key,
    )


def send_review_submitted_email(
    *, to: str, article_title: str, reviewer_name: str, report_url: str
) -> None:
    template = _require_template(
        settings.resend_review_submitted_template,
        "قالب بريد تسليم المراجعة غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال تنبيه تسليم المراجعة.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "REVIEWER_NAME": reviewer_name,
            "REPORT_URL": report_url,
            **_common_variables(),
        },
    )


def send_decision_email(
    *,
    to: str,
    article_title: str,
    decision_text: str,
    article_url: str,
    next_step: str,
) -> None:
    template = _require_template(
        settings.resend_decision_template,
        "قالب بريد القرار التحريري غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد القرار التحريري.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "DECISION_TEXT": decision_text,
            "ARTICLE_URL": article_url,
            "NEXT_STEP": next_step,
            **_common_variables(),
        },
    )


def send_article_published_email(
    *, to: str, article_title: str, article_url: str
) -> None:
    template = _require_template(
        settings.resend_article_published_template,
        "قالب بريد نشر المقال غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال بريد نشر المقال.",
        template_alias_or_id=template,
        variables={
            "ARTICLE_TITLE": article_title,
            "ARTICLE_URL": article_url,
            **_common_variables(),
        },
    )


def send_unread_notifications_digest_email(
    *, to: str, unread_count: int, notifications_url: str
) -> None:
    template = _require_template(
        settings.resend_unread_notifications_digest_template,
        "قالب ملخص الإشعارات غير مُهيّأ على الخادم.",
    )
    _send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال ملخص الإشعارات.",
        template_alias_or_id=template,
        variables={
            "UNREAD_COUNT": unread_count,
            "NOTIFICATIONS_URL": notifications_url,
            **_common_variables(),
        },
    )


def send_invitation_email(
    *,
    to: str,
    article_title: str,
    role: InvitationRole,
    token: str,
    expires_at: datetime,
    review_due_text: str = "",
) -> None:
    role_label = _ROLE_LABELS.get(role, role.value)
    link = f"{settings.frontend_base_url.rstrip('/')}/daawa/{token}"
    expires_text = format_date_time(expires_at)
    if settings.resend_review_invitation_template:
        _send_resend_email(
            to=to,
            failure_detail="تعذّر إرسال بريد الدعوة، حاول مجدداً.",
            template_alias_or_id=settings.resend_review_invitation_template,
            variables={
                "ARTICLE_TITLE": article_title,
                "ROLE_LABEL": role_label,
                "INVITATION_URL": link,
                "EXPIRES_TEXT": expires_text,
                "DUE_TEXT": review_due_text,
                **_common_variables(),
            },
        )
        return

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
