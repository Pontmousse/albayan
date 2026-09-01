import * as React from "react";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  ARTICLE_URL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function Published({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  ARTICLE_URL = resendTemplateVariable("ARTICLE_URL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="نُشر بحثكم في مجلة البيان"
      title="نشر البحث"
      intro={<>يسر مجلة البيان إشعاركم بنشر بحثكم: «{ARTICLE_TITLE}».</>}
      actionHref={ARTICLE_URL}
      actionLabel="متابعة البحث"
      fallbackHref={ARTICLE_URL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    />
  );
}

Published.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  ARTICLE_URL: "https://albayan-journal.org/maktabi/maqalati/article-id",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
