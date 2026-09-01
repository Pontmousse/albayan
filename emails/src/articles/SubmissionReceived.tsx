import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  ARTICLE_URL?: string;
  SUBMITTED_TEXT?: string;
  VERSION_NUMBER?: string | number;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function SubmissionReceived({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  ARTICLE_URL = resendTemplateVariable("ARTICLE_URL"),
  SUBMITTED_TEXT = resendTemplateVariable("SUBMITTED_TEXT"),
  VERSION_NUMBER = resendTemplateVariable("VERSION_NUMBER"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="تم استلام بحثكم في مجلة البيان"
      title="تم استلام بحثكم بنجاح"
      intro={<>استلمنا بحثكم: «{ARTICLE_TITLE}».</>}
      actionHref={ARTICLE_URL}
      actionLabel="متابعة البحث"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        رقم النسخة: {VERSION_NUMBER}
        <br />
        وقت التقديم: {SUBMITTED_TEXT}
      </Text>
    </EmailMessage>
  );
}

SubmissionReceived.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  ARTICLE_URL: "https://albayan-journal.org/maktabi/maqalati/article-id",
  SUBMITTED_TEXT: "١٨ ربيع الأول ١٤٤٨ هـ، ١٢:٤٥",
  VERSION_NUMBER: 1,
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
