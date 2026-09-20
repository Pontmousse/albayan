import * as React from "react";
import { Section, Text } from "react-email";
import { AlbayanLayout } from "../_components/AlbayanLayout";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  colors,
  fontFamily,
  resendTemplateVariable,
} from "../_components/theme";

export type DonationReceivedProps = {
  AMOUNT_TEXT?: string;
  DONATION_REFERENCE?: string;
  DATE_TEXT?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export function DonationReceived({
  AMOUNT_TEXT = resendTemplateVariable("AMOUNT_TEXT"),
  DONATION_REFERENCE = resendTemplateVariable("DONATION_REFERENCE"),
  DATE_TEXT = resendTemplateVariable("DATE_TEXT"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: DonationReceivedProps) {
  return (
    <AlbayanLayout
      preview="جزاكم الله خيرًا وبارك فيكم على دعم مجلة البيان"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
      dateText={DATE_TEXT}
    >
      <Section style={{ padding: "20px 34px 8px", textAlign: "center" }}>
        <Text
          className="email-title"
          style={{
            color: colors.accentStrong,
            fontFamily,
            fontSize: "28px",
            fontWeight: 700,
            lineHeight: "1.6",
            margin: "0 0 14px",
          }}
        >
          جزاكم الله خيرًا وبارك فيكم
        </Text>
        <Text
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "16px",
            lineHeight: "2",
            margin: "0",
          }}
        >
          تم استلام مساهمتكم الاختيارية بنجاح.
        </Text>
      </Section>
      <Section
        style={{
          backgroundColor: colors.paper,
          border: `1px solid ${colors.border}`,
          borderRadius: "14px",
          margin: "10px 34px 18px",
          padding: "16px 18px",
          textAlign: "center",
        }}
      >
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "13px",
            lineHeight: "1.8",
            margin: "0 0 4px",
          }}
        >
          قيمة المساهمة
        </Text>
        <Text
          dir="ltr"
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "24px",
            fontWeight: 700,
            lineHeight: "1.5",
            margin: 0,
          }}
        >
          {AMOUNT_TEXT}
        </Text>
      </Section>
      <Section
        style={{
          backgroundColor: colors.paper,
          border: `1px solid ${colors.border}`,
          borderRadius: "14px",
          margin: "10px 34px 18px",
          padding: "16px 18px",
          textAlign: "center",
        }}
      >
        <Text
          style={{
            color: colors.accentStrong,
            fontFamily,
            fontSize: "15px",
            lineHeight: "2",
            margin: 0,
          }}
        >
          نسأل الله أن يبارك فيكم وفي أهليكم، وأن ينفع بكم، ويجزيكم خير الجزاء، ويجعل مساهمتكم عونًا على نشر العلم النافع وخدمة أهله.
        </Text>
      </Section>
      <Section
        style={{
          backgroundColor: colors.paper,
          border: `1px solid ${colors.border}`,
          borderRadius: "14px",
          margin: "10px 34px 18px",
          padding: "14px 18px",
          textAlign: "center",
        }}
      >
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "13px",
            lineHeight: "1.9",
            margin: "0 0 6px",
          }}
        >
          مرجع المساهمة
        </Text>
        <Text
          dir="ltr"
          style={{
            color: colors.muted,
            fontFamily: "Consolas, Monaco, 'Courier New', monospace",
            fontSize: "12px",
            lineHeight: "1.7",
            margin: 0,
            overflowWrap: "anywhere",
            wordBreak: "break-all",
          }}
        >
          {DONATION_REFERENCE}
        </Text>
      </Section>
      <Section style={{ padding: "0 34px 12px", textAlign: "right" }}>
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "14px",
            lineHeight: "2",
            margin: 0,
          }}
        >
          خدمات مجلة البيان العلمية متاحة دون مقابل، والمساهمة اختيارية ولا تؤثر في التقديم أو التحكيم أو القرار التحريري أو النشر. هذه الرسالة تأكيد لاستلام المساهمة وليست إيصالًا ضريبيًا أو شهادة تبرع خيري.
        </Text>
      </Section>
    </AlbayanLayout>
  );
}

DonationReceived.PreviewProps = {
  AMOUNT_TEXT: "25.00 CAD",
  DONATION_REFERENCE: "cs_test_example_reference_that_wraps_cleanly_on_mobile",
  DATE_TEXT: "١ ربيع الأول ١٤٤٨ هـ",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "https://albayan-journal.org/email",
} satisfies DonationReceivedProps;

export default DonationReceived;
