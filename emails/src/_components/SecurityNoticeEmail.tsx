import * as React from "react";
import { Heading, Section, Text } from "react-email";
import { AlbayanLayout } from "./AlbayanLayout";
import { GoldDivider } from "./GoldDivider";
import {
  colors,
  displayFontFamily,
  fontFamily,
} from "./theme";

type SecurityNoticeEmailProps = {
  preview: string;
  title: string;
  message: string;
  guidance: string;
  recipientEmail: string;
  siteUrl: string;
  contactEmail: string;
  assetBaseUrl: string;
};

export function SecurityNoticeEmail({
  preview,
  title,
  message,
  guidance,
  recipientEmail,
  siteUrl,
  contactEmail,
  assetBaseUrl,
}: SecurityNoticeEmailProps) {
  return (
    <AlbayanLayout
      preview={preview}
      siteUrl={siteUrl}
      contactEmail={contactEmail}
      assetBaseUrl={assetBaseUrl}
    >
      <Section
        className="email-content"
        style={{ padding: "28px 34px 10px", textAlign: "center" }}
      >
        <GoldDivider spacing={22} assetBaseUrl={assetBaseUrl} />
        <Heading
          className="email-title"
          as="h1"
          style={{
            color: colors.accentStrong,
            fontFamily: displayFontFamily,
            fontSize: "32px",
            fontWeight: 700,
            lineHeight: "1.45",
            margin: 0,
            textAlign: "center",
          }}
        >
          {title}
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
          {message}
        </Text>
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "14px",
            lineHeight: "1.9",
            margin: "14px 0 0",
            textAlign: "center",
          }}
        >
          الحساب المرتبط بالبريد:
          <br />
          <strong dir="ltr" style={{ overflowWrap: "anywhere" }}>
            {recipientEmail}
          </strong>
        </Text>
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "13px",
            lineHeight: "1.9",
            margin: "18px 0 0",
            textAlign: "center",
          }}
        >
          {guidance}
        </Text>
      </Section>
    </AlbayanLayout>
  );
}
