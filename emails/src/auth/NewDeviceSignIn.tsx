import * as React from "react";
import { SecurityNoticeEmail } from "../_components/SecurityNoticeEmail";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  resendTemplateVariable,
} from "../_components/theme";

type NewDeviceSignInEmailProps = {
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function NewDeviceSignInEmail({
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: NewDeviceSignInEmailProps) {
  return (
    <SecurityNoticeEmail
      preview="تسجيل دخول إلى حسابكم في مجلة البيان من جهاز جديد"
      title="تسجيل دخول من جهاز جديد"
      message="رصد نظام الحماية تسجيل دخول ناجحًا إلى حسابكم من جهاز لم يُتعرّف عليه سابقًا."
      guidance="إن كنتم أنتم من سجل الدخول فلا يلزم اتخاذ أي إجراء. وإن لم تتعرفوا على هذا النشاط، فغيّروا كلمة المرور فورًا وراجعوا جلسات الحساب وطرق تسجيل الدخول المرتبطة به."
      recipientEmail={RECIPIENT_EMAIL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

NewDeviceSignInEmail.PreviewProps = {
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies NewDeviceSignInEmailProps;
