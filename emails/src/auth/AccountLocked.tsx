import * as React from "react";
import { SecurityNoticeEmail } from "../_components/SecurityNoticeEmail";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  resendTemplateVariable,
} from "../_components/theme";

type AccountLockedEmailProps = {
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function AccountLockedEmail({
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: AccountLockedEmailProps) {
  return (
    <SecurityNoticeEmail
      preview="تم قفل حسابكم مؤقتًا في مجلة البيان"
      title="تم قفل الحساب مؤقتًا"
      message="قُفل حسابكم مؤقتًا بعد تكرار محاولات تسجيل الدخول غير الناجحة. سيبقى حسابكم وبياناتكم محفوظين، ويمكنكم المحاولة مجددًا بعد انتهاء مدة القفل التي يحددها نظام الحماية."
      guidance="إن لم تكونوا أنتم من قام بهذه المحاولات، فننصح بتغيير كلمة المرور عند استعادة الوصول إلى الحساب والتواصل معنا إذا ساوركم أي قلق أمني."
      recipientEmail={RECIPIENT_EMAIL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

AccountLockedEmail.PreviewProps = {
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies AccountLockedEmailProps;
