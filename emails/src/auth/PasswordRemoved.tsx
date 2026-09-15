import * as React from "react";
import { SecurityNoticeEmail } from "../_components/SecurityNoticeEmail";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  resendTemplateVariable,
} from "../_components/theme";

type PasswordRemovedEmailProps = {
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function PasswordRemovedEmail({
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: PasswordRemovedEmailProps) {
  return (
    <SecurityNoticeEmail
      preview="تمت إزالة كلمة المرور من حسابكم في مجلة البيان"
      title="تمت إزالة كلمة المرور"
      message="أزيلت طريقة تسجيل الدخول بكلمة المرور من حسابكم. يلزم الآن استخدام إحدى طرق تسجيل الدخول الأخرى المرتبطة بالحساب."
      guidance="إن لم تقوموا بهذا التغيير، فراجعوا إعدادات الأمان وطرق تسجيل الدخول المرتبطة بالحساب وتواصلوا معنا إذا ساوركم أي قلق أمني."
      recipientEmail={RECIPIENT_EMAIL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

PasswordRemovedEmail.PreviewProps = {
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies PasswordRemovedEmailProps;
