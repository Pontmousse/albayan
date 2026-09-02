import * as React from "react";
import { Body, Container, Head, Html, Preview, Section, Text } from "react-email";
import { AlbayanFooter } from "./AlbayanFooter";
import { AlbayanHeader } from "./AlbayanHeader";
import { colors, fontFamily, resendTemplateVariable } from "./theme";

type AlbayanLayoutProps = {
  preview: string;
  siteUrl: string;
  contactEmail: string;
  assetBaseUrl?: string;
  dateText?: string;
  children: React.ReactNode;
};

export function AlbayanLayout({
  preview,
  siteUrl,
  contactEmail,
  assetBaseUrl,
  dateText = resendTemplateVariable("DATE_TEXT"),
  children,
}: AlbayanLayoutProps) {
  return (
    <Html lang="ar" dir="rtl">
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>{`
          .email-container, .email-content, .email-action-button { box-sizing: border-box; }
          .email-fluid-image { height: auto !important; max-width: 100% !important; }
          @media only screen and (max-width: 620px) {
            .email-body { padding: 0 !important; }
            .email-container { border-radius: 0 !important; width: 100% !important; }
            .email-content { padding: 24px 18px 8px !important; }
            .email-title { font-size: 26px !important; line-height: 1.5 !important; }
            .email-action-button { font-size: 16px !important; padding: 13px 22px !important; }
            .email-feature-cell { box-sizing: border-box !important; display: block !important; width: 100% !important; }
            .email-footer-corner-cell { padding-left: 2px !important; padding-right: 2px !important; padding-top: 162px !important; width: 16% !important; }
            .email-footer-center-cell { width: 68% !important; }
            .email-otp-code { font-size: 28px !important; letter-spacing: 5px !important; padding: 16px 12px !important; }
          }
        `}</style>
      </Head>
      <Preview>{preview}</Preview>
      <Body
        className="email-body"
        lang="ar"
        dir="rtl"
        style={{
          backgroundColor: colors.paper,
          color: colors.ink,
          fontFamily,
          margin: 0,
          padding: "28px 12px",
          textAlign: "right",
        }}
      >
        <Container
          className="email-container"
          style={{
            backgroundColor: colors.white,
            border: `1px solid ${colors.border}`,
            borderRadius: "18px",
            boxShadow: "0 18px 48px rgba(23, 35, 28, 0.10)",
            maxWidth: "600px",
            overflow: "hidden",
            width: "100%",
          }}
        >
          <AlbayanHeader assetBaseUrl={assetBaseUrl} />
          <Section
            className="email-content"
            style={{ padding: "24px 34px 0", textAlign: "center" }}
          >
            <Text
              style={{
                color: colors.muted,
                fontFamily,
                fontSize: "13px",
                lineHeight: "1.9",
                margin: "0 0 12px",
              }}
            >
              بتاريخ {dateText}
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
              بسم الله الرحمن الرحيم، والصلاة والسلام على رسول الله
              <br />
              السلام عليكم ورحمة الله وبركاته، أما بعد:
            </Text>
          </Section>
          {children}
          <Section style={{ padding: "0 34px 24px", textAlign: "center" }}>
            <Text
              style={{
                color: colors.accentStrong,
                fontFamily,
                fontSize: "16px",
                fontWeight: 700,
                lineHeight: "2",
                margin: "10px 0 0",
              }}
            >
              جزاكم الله خيرًا.
            </Text>
          </Section>
          <AlbayanFooter
            siteUrl={siteUrl}
            contactEmail={contactEmail}
            assetBaseUrl={assetBaseUrl}
          />
        </Container>
      </Body>
    </Html>
  );
}
