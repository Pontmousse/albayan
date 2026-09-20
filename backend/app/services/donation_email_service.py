"""Arabic donor acknowledgement through the existing Al-Bayan email transport."""

import html as html_lib

from app.core.config import settings
from app.services import email_service


def send_donation_received_email(
    *,
    to: str,
    amount_text: str,
    donation_reference: str,
    idempotency_key: str,
) -> str | None:
    template = settings.resend_donation_received_template.strip()
    variables = {
        "AMOUNT_TEXT": amount_text,
        "DONATION_REFERENCE": donation_reference,
        **email_service._common_variables(),
    }

    if template:
        return email_service._send_resend_email(
            to=to,
            failure_detail="تعذّر إرسال رسالة تأكيد المساهمة.",
            template_alias_or_id=template,
            variables=variables,
            idempotency_key=idempotency_key,
        )

    safe_amount = html_lib.escape(amount_text)
    safe_reference = html_lib.escape(donation_reference)
    site_url = html_lib.escape(settings.frontend_base_url.rstrip("/"), quote=True)
    html = f"""
    <div dir="rtl" lang="ar" style="font-family:Arial,sans-serif;line-height:2;text-align:right">
      <h2>جزاكم الله خيرًا وبارك فيكم</h2>
      <p>تم استلام مساهمتكم الاختيارية بمقدار <strong>{safe_amount}</strong>.</p>
      <p>نسأل الله أن يبارك فيكم وفي أهليكم، وأن ينفع بكم، ويجزيكم خير الجزاء، ويجعل مساهمتكم عونًا على نشر العلم النافع وخدمة أهله.</p>
      <p>المرجع: <strong>{safe_reference}</strong></p>
      <p>خدمات مجلة البيان العلمية متاحة دون مقابل، ولا تؤثر المساهمات في التقديم أو التحكيم أو القرار التحريري أو النشر.</p>
      <p><a href="{site_url}">مجلة البيان</a></p>
    </div>
    """
    return email_service._send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رسالة تأكيد المساهمة.",
        subject="جزاكم الله خيرًا على دعم مجلة البيان",
        html=html,
        idempotency_key=idempotency_key,
    )
