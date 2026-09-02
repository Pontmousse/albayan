import * as React from "react";
import { Heading, Section, Text } from "react-email";
import { AlbayanLayout } from "../_components/AlbayanLayout";
import { GoldDivider } from "../_components/GoldDivider";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  colors,
  displayFontFamily,
  fontFamily,
  resendTemplateVariable,
} from "../_components/theme";

type VerificationCodeEmailProps = {
  OTP_CODE?: string;
  RECIPIENT_EMAIL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function VerificationCodeEmail({
  OTP_CODE = resendTemplateVariable("OTP_CODE"),
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: VerificationCodeEmailProps) {
  return (
    <AlbayanLayout
      preview="رمز التحقق من بريدكم في مجلة البيان"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Section className="email-content" style={{ padding: "28px 34px 10px", textAlign: "center" }}>
        <GoldDivider spacing={22} assetBaseUrl={ASSET_BASE_URL} />
        <Heading
          className="email-title"
          as="h1"
          style={{
            color: colors.accentStrong,
            fontFamily: displayFontFamily,
            fontSize: "32px",
            fontWeight: 700,
            lineHeight: "1.45",
            margin: "0",
            textAlign: "center",
          }}
        >
          رمز التحقق من البريد الإلكتروني
        </Heading>
        <Text
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "16px",
            lineHeight: "2",
            margin: "22px 0 0",
            textAlign: "center",
          }}
        >
          استخدموا الرمز الآتي لإتمام إنشاء حسابكم في مجلة البيان للبريد:
          <br />
          <strong dir="ltr" style={{ overflowWrap: "anywhere" }}>
            {RECIPIENT_EMAIL}
          </strong>
        </Text>
        <Text
          className="email-otp-code"
          style={{
            backgroundColor: colors.accentSoft,
            border: `1px solid ${colors.border}`,
            borderRadius: "16px",
            color: colors.accentStrong,
            direction: "ltr",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: "34px",
            fontWeight: 700,
            letterSpacing: "8px",
            lineHeight: "1.4",
            margin: "24px auto",
            padding: "18px 22px",
            textAlign: "center",
          }}
        >
          {OTP_CODE}
        </Text>
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "13px",
            lineHeight: "1.9",
            margin: "0",
            textAlign: "center",
          }}
        >
          إن لم تطلبوا إنشاء حساب، يمكنكم تجاهل هذه الرسالة.
        </Text>
      </Section>
    </AlbayanLayout>
  );
}

VerificationCodeEmail.PreviewProps = {
  OTP_CODE: "123456",
  RECIPIENT_EMAIL: "person@example.com",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies VerificationCodeEmailProps;
