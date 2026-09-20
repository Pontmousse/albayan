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
    <div dir="rtl" lang="ar" style="margin:0;padding:0;background:#f5f2e8;font-family:Arial,Tahoma,sans-serif;color:#1f2925;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;margin:0;padding:0;background:#f5f2e8;">
        <tr>
          <td align="center" style="padding:28px 14px;">
            <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:600px;background:#ffffff;border:1px solid #ded8c7;border-radius:18px;overflow:hidden;">
              <tr>
                <td style="padding:22px 28px 16px;text-align:center;background:#173f35;border-bottom:4px solid #b08b35;">
                  <div style="font-size:15px;line-height:1.8;color:#e8dfc3;">مجلة البيان</div>
                  <div style="font-size:13px;line-height:1.8;color:#c9d7d2;">شكرًا لمساهمتكم في دعم نشر العلم النافع</div>
                </td>
              </tr>
              <tr>
                <td style="padding:30px 28px 10px;text-align:center;">
                  <div style="font-size:28px;font-weight:700;line-height:1.7;color:#235a4d;margin:0 0 12px;">جزاكم الله خيرًا وبارك فيكم</div>
                  <div style="font-size:16px;line-height:2;color:#39443f;">تم استلام مساهمتكم الاختيارية بنجاح.</div>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 28px 8px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#fbfaf6;border:1px solid #e6dfcd;border-radius:14px;">
                    <tr>
                      <td style="padding:16px 18px;text-align:center;">
                        <div style="font-size:13px;line-height:1.8;color:#7c7669;margin-bottom:4px;">قيمة المساهمة</div>
                        <div dir="ltr" style="font-size:24px;font-weight:700;line-height:1.5;color:#1f2925;unicode-bidi:embed;">{safe_amount}</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 28px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#f0f7f3;border:1px solid #cfe0d8;border-radius:14px;">
                    <tr>
                      <td style="padding:18px 20px;text-align:center;font-size:16px;line-height:2.1;color:#235a4d;">
                        نسأل الله أن يبارك فيكم وفي أهليكم، وأن ينفع بكم، ويجزيكم خير الجزاء، ويجعل مساهمتكم عونًا على نشر العلم النافع وخدمة أهله.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 28px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#fbfaf6;border:1px solid #e6dfcd;border-radius:14px;">
                    <tr>
                      <td style="padding:14px 18px;text-align:center;">
                        <div style="font-size:12px;line-height:1.8;color:#8a8375;margin-bottom:6px;">مرجع المساهمة</div>
                        <div dir="ltr" style="font-family:Consolas,Monaco,'Courier New',monospace;font-size:12px;line-height:1.7;color:#555f5b;word-break:break-all;overflow-wrap:anywhere;unicode-bidi:embed;">{safe_reference}</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="padding:18px 28px 8px;text-align:right;font-size:13px;line-height:2;color:#6e746f;">
                  خدمات مجلة البيان العلمية متاحة دون مقابل، والمساهمة اختيارية ولا تؤثر في التقديم أو التحكيم أو القرار التحريري أو النشر.
                </td>
              </tr>
              <tr>
                <td style="padding:10px 28px 28px;text-align:center;">
                  <a href="{site_url}" style="display:inline-block;background:#235a4d;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;line-height:1.4;padding:12px 22px;border-radius:10px;">زيارة مجلة البيان</a>
                </td>
              </tr>
            </table>
            <div style="max-width:600px;margin:14px auto 0;text-align:center;font-size:11px;line-height:1.8;color:#8a8375;">
              هذه الرسالة تأكيد لاستلام المساهمة وليست إيصالًا ضريبيًا أو شهادة تبرع خيري.
            </div>
          </td>
        </tr>
      </table>
    </div>
    """
    return email_service._send_resend_email(
        to=to,
        failure_detail="تعذّر إرسال رسالة تأكيد المساهمة.",
        subject="جزاكم الله خيرًا على دعم مجلة البيان",
        html=html,
        idempotency_key=idempotency_key,
    )
