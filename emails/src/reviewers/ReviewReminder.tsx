import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  REVIEW_URL?: string;
  DUE_TEXT?: string;
  REMINDER_TEXT?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function ReviewReminder({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  REVIEW_URL = resendTemplateVariable("REVIEW_URL"),
  DUE_TEXT = resendTemplateVariable("DUE_TEXT"),
  REMINDER_TEXT = resendTemplateVariable("REMINDER_TEXT"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="تذكير بمراجعة بحث في مجلة البيان"
      title="تذكير لطيف بالمراجعة"
      intro={<>نذكّركم بالمراجعة المسندة إليكم للبحث: «{ARTICLE_TITLE}».</>}
      actionHref={REVIEW_URL}
      actionLabel="فتح المراجعة"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        {REMINDER_TEXT}
        <br />
        الموعد المحدد: {DUE_TEXT}
      </Text>
    </EmailMessage>
  );
}

ReviewReminder.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  REVIEW_URL: "https://albayan-journal.org/maktabi/murajaati/assignment-id",
  DUE_TEXT: "٢٥ ربيع الأول ١٤٤٨ هـ",
  REMINDER_TEXT: "بلغت المراجعة منتصف المهلة المحددة.",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
