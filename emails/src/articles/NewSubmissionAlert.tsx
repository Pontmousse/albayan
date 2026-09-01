import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  AUTHOR_NAME?: string;
  ARTICLE_URL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function NewSubmissionAlert({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  AUTHOR_NAME = resendTemplateVariable("AUTHOR_NAME"),
  ARTICLE_URL = resendTemplateVariable("ARTICLE_URL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="بحث جديد بانتظار المتابعة التحريرية"
      title="بحث جديد في لوحة التحرير"
      intro={<>قُدّم بحث جديد بعنوان: «{ARTICLE_TITLE}».</>}
      actionHref={ARTICLE_URL}
      actionLabel="فتح البحث"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        المؤلف/المقدّم: <strong>{AUTHOR_NAME}</strong>
      </Text>
    </EmailMessage>
  );
}

NewSubmissionAlert.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  AUTHOR_NAME: "د. أحمد",
  ARTICLE_URL: "https://albayan-journal.org/admin/maqalat/article-id",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
