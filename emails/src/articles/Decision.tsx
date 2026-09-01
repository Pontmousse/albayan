import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  DECISION_TEXT?: string;
  ARTICLE_URL?: string;
  NEXT_STEP?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function Decision({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  DECISION_TEXT = resendTemplateVariable("DECISION_TEXT"),
  ARTICLE_URL = resendTemplateVariable("ARTICLE_URL"),
  NEXT_STEP = resendTemplateVariable("NEXT_STEP"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="صدر تحديث تحريري على بحثكم"
      title="قرار تحريري"
      intro={<>صدر قرار تحريري على بحثكم «{ARTICLE_TITLE}»: {DECISION_TEXT}.</>}
      actionHref={ARTICLE_URL}
      actionLabel="فتح البحث"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        {NEXT_STEP}
      </Text>
    </EmailMessage>
  );
}

Decision.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  DECISION_TEXT: "قبول",
  ARTICLE_URL: "https://albayan-journal.org/maktabi/maqalati/article-id",
  NEXT_STEP: "يرجى متابعة لوحة المقال لأي تعليمات نهائية قبل النشر.",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
