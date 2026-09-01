import * as React from "react";
import { Text } from "react-email";
import { EmailMessage } from "../_components/EmailMessage";
import { ASSET_BASE_URL_PLACEHOLDER, fontFamily, resendTemplateVariable } from "../_components/theme";

type Props = {
  ARTICLE_TITLE?: string;
  REVIEWER_NAME?: string;
  REPORT_URL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function ReviewSubmitted({
  ARTICLE_TITLE = resendTemplateVariable("ARTICLE_TITLE"),
  REVIEWER_NAME = resendTemplateVariable("REVIEWER_NAME"),
  REPORT_URL = resendTemplateVariable("REPORT_URL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: Props) {
  return (
    <EmailMessage
      preview="تم تسليم مراجعة جديدة"
      title="تقرير مراجعة جديد"
      intro={<>سلّم {REVIEWER_NAME} تقرير مراجعة للبحث: «{ARTICLE_TITLE}».</>}
      actionHref={REPORT_URL}
      actionLabel="فتح تقرير المراجعة"
      fallbackHref={REPORT_URL}
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Text style={{ fontFamily, fontSize: "16px", lineHeight: "2", textAlign: "center" }}>
        يمكنكم الآن متابعة القرار التحريري أو انتظار بقية التقارير.
      </Text>
    </EmailMessage>
  );
}

ReviewSubmitted.PreviewProps = {
  ARTICLE_TITLE: "أثر المخطوطات العلمية في بناء المعرفة",
  REVIEWER_NAME: "د. مراجع",
  REPORT_URL: "https://albayan-journal.org/maktabi/tahriri/article-id",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies Props;
