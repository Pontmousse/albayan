import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  UNREAD_COUNT?: string | number;
  NOTIFICATIONS_URL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function UnreadDigest({
  UNREAD_COUNT = resendTemplateVariable("UNREAD_COUNT"),
  NOTIFICATIONS_URL = resendTemplateVariable("NOTIFICATIONS_URL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="لديكم إشعارات غير مقروءة في مجلة البيان"
      title="إشعارات تنتظر اطلاعكم"
      intro={<>لديكم {UNREAD_COUNT} إشعارات غير مقروءة في منصة مجلة البيان.</>}
      actionHref={NOTIFICATIONS_URL}
      actionLabel="فتح الإشعارات"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        لن نكرر هذا التذكير أكثر من مرة أسبوعيًا ما دامت الإشعارات غير مقروءة.
      </Text>
    </EmailMessage>
  );
}

UnreadDigest.PreviewProps = {
  UNREAD_COUNT: 6,
  NOTIFICATIONS_URL: "https://albayan-journal.org/maktabi/isharat",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
