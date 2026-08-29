import * as React from "react";
import { Body, Container, Head, Html, Preview } from "react-email";
import { AlbayanFooter } from "./AlbayanFooter";
import { AlbayanHeader } from "./AlbayanHeader";
import { colors, fontFamily } from "./theme";

type AlbayanLayoutProps = {
  preview: string;
  siteUrl: string;
  assetBaseUrl?: string;
  children: React.ReactNode;
};

export function AlbayanLayout({
  preview,
  siteUrl,
  assetBaseUrl,
  children,
}: AlbayanLayoutProps) {
  return (
    <Html lang="ar" dir="rtl">
      <Head />
      <Preview>{preview}</Preview>
      <Body
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
          {children}
          <AlbayanFooter siteUrl={siteUrl} assetBaseUrl={assetBaseUrl} />
        </Container>
      </Body>
    </Html>
  );
}
