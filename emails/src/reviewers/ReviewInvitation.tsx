import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  ROLE_LABEL?: string;
  INVITATION_URL?: string;
  EXPIRES_TEXT?: string;
  DUE_TEXT?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function ReviewInvitation({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  ROLE_LABEL = resendTemplateVariable("ROLE_LABEL"),
  INVITATION_URL = resendTemplateVariable("INVITATION_URL"),
  EXPIRES_TEXT = resendTemplateVariable("EXPIRES_TEXT"),
  DUE_TEXT = resendTemplateVariable("DUE_TEXT"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="دعوة للمشاركة في تحكيم بحث"
      title="دعوة للمشاركة العلمية"
      intro={<>دُعيتم بدور {ROLE_LABEL} للمشاركة في البحث: «{ARTICLE_TITLE}».</>}
      actionHref={INVITATION_URL}
      actionLabel="قبول الدعوة"
      fallbackHref={INVITATION_URL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        تنتهي صلاحية رابط الدعوة في: {EXPIRES_TEXT}
        <br />
        {DUE_TEXT ? <>موعد المراجعة المقترح: {DUE_TEXT}</> : null}
      </Text>
    </EmailMessage>
  );
}

ReviewInvitation.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  ROLE_LABEL: "مراجع",
  INVITATION_URL: "https://albayan-journal.org/daawa/token",
  EXPIRES_TEXT: "١٨ ربيع الأول ١٤٤٨ هـ، ١٢:٤٥",
  DUE_TEXT: "٢٥ ربيع الأول ١٤٤٨ هـ",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
