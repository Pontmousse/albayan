import * as React from "react";
import { Heading, Link, Section, Text } from "react-email";
import { ActionButton } from "./ActionButton";
import { AlbayanLayout } from "./AlbayanLayout";
import { GoldDivider } from "./GoldDivider";
import { InfoPanel } from "./InfoPanel";
import { colors, displayFontFamily, fontFamily } from "./theme";

type EmailMessageProps = {
  preview: string;
  title: string;
  intro?: React.ReactNode;
  children?: React.ReactNode;
  actionHref?: string;
  actionLabel?: string;
  fallbackHref?: string;
  footerNote?: React.ReactNode;
  siteUrl: string;
  contactEmail: string;
  assetBaseUrl?: string;
};

export function EmailMessage({
  preview,
  title,
  intro,
  children,
  actionHref,
  actionLabel,
  fallbackHref,
  footerNote,
  siteUrl,
  contactEmail,
  assetBaseUrl,
}: EmailMessageProps) {
  return (
    <AlbayanLayout
      preview={preview}
      siteUrl={siteUrl}
      contactEmail={contactEmail}
      assetBaseUrl={assetBaseUrl}
    >
      <Section style={{ padding: "28px 34px 10px", textAlign: "center" }}>
        <Text
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "16px",
            lineHeight: "2",
            margin: "0",
            textAlign: "center",
          }}
        >
          السلام عليكم ورحمة الله وبركاته
        </Text>
        <GoldDivider spacing={22} assetBaseUrl={assetBaseUrl} />
        <Heading
          as="h1"
          style={{
            color: colors.accentStrong,
            fontFamily: displayFontFamily,
            fontSize: "30px",
            fontWeight: 700,
            lineHeight: "1.45",
            margin: "0",
            textAlign: "center",
          }}
        >
          {title}
        </Heading>
        {intro ? <InfoPanel>{intro}</InfoPanel> : null}
        {children}
        {actionHref && actionLabel ? (
          <ActionButton href={actionHref}>{actionLabel}</ActionButton>
        ) : null}
        {fallbackHref ? (
          <Text
            style={{
              color: colors.muted,
              fontFamily,
              fontSize: "13px",
              lineHeight: "1.9",
              margin: "0",
              overflowWrap: "break-word",
              textAlign: "center",
            }}
          >
            إن لم يعمل الزر، افتح هذا الرابط مباشرة:
            <br />
            <Link
              href={fallbackHref}
              style={{
                color: colors.accent,
                fontFamily,
                textDecoration: "underline",
              }}
            >
              {fallbackHref}
            </Link>
          </Text>
        ) : null}
        {footerNote ? (
          <Text
            style={{
              color: colors.muted,
              fontFamily,
              fontSize: "13px",
              lineHeight: "1.9",
              margin: "14px 0 0",
              textAlign: "center",
            }}
          >
            {footerNote}
          </Text>
        ) : null}
      </Section>
    </AlbayanLayout>
  );
}
