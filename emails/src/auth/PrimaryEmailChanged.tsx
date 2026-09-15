import * as React from "react";
import { SecurityNoticeEmail } from "../_components/SecurityNoticeEmail";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  resendTemplateVariable,
} from "../_components/theme";

type PrimaryEmailChangedEmailProps = {
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function PrimaryEmailChangedEmail({
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: PrimaryEmailChangedEmailProps) {
  return (
    <SecurityNoticeEmail
      preview="تم تغيير البريد الإلكتروني الأساسي في مجلة البيان"
      title="تم تغيير البريد الإلكتروني الأساسي"
      message="تم تغيير البريد الإلكتروني الأساسي المرتبط بحسابكم في مجلة البيان."
      guidance="إن لم تقوموا بهذا التغيير، فأمّنوا الحساب فورًا وراجعوا بياناته وطرق تسجيل الدخول المرتبطة به، ثم تواصلوا معنا إذا احتجتم إلى المساعدة."
      recipientEmail={RECIPIENT_EMAIL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

PrimaryEmailChangedEmail.PreviewProps = {
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies PrimaryEmailChangedEmailProps;
