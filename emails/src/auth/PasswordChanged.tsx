import * as React from "react";
import { SecurityNoticeEmail } from "../_components/SecurityNoticeEmail";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  resendTemplateVariable,
} from "../_components/theme";

type PasswordChangedEmailProps = {
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function PasswordChangedEmail({
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: PasswordChangedEmailProps) {
  return (
    <SecurityNoticeEmail
      preview="تم تغيير كلمة مرور حسابكم في مجلة البيان"
      title="تم تغيير كلمة المرور"
      message="تم تغيير كلمة مرور حسابكم في مجلة البيان بنجاح. إذا كنتم أنتم من أجرى هذا التغيير فلا يلزم اتخاذ أي إجراء إضافي."
      guidance="إن لم تقوموا بهذا التغيير، فغيّروا كلمة المرور فورًا، وراجعوا جلسات الحساب، وتواصلوا معنا إذا تعذر عليكم تأمين الحساب."
      recipientEmail={RECIPIENT_EMAIL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

PasswordChangedEmail.PreviewProps = {
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies PasswordChangedEmailProps;
