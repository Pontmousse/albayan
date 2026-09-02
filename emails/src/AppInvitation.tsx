import * as React from "react";
import { Heading, Section, Text } from "react-email";
import { ActionButton } from "./_components/ActionButton";
import { AlbayanLayout } from "./_components/AlbayanLayout";
import { GoldDivider } from "./_components/GoldDivider";
import { InfoPanel } from "./_components/InfoPanel";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  colors,
  displayFontFamily,
  fontFamily,
  resendTemplateVariable,
} from "./_components/theme";

type AppInvitationEmailProps = {
  INVITATION_URL?: string;
  RECIPIENT_NAME?: string;
  RECIPIENT_EMAIL?: string;
  EXPIRES_TEXT?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function AppInvitationEmail({
  INVITATION_URL = resendTemplateVariable("INVITATION_URL"),
  RECIPIENT_NAME = resendTemplateVariable("RECIPIENT_NAME"),
  RECIPIENT_EMAIL = resendTemplateVariable("RECIPIENT_EMAIL"),
  EXPIRES_TEXT = resendTemplateVariable("EXPIRES_TEXT"),
  SITE_URL = resendTemplateVariable("SITE_URL"),
  CONTACT_EMAIL = resendTemplateVariable("CONTACT_EMAIL"),
  ASSET_BASE_URL = ASSET_BASE_URL_PLACEHOLDER,
}: AppInvitationEmailProps) {
  return (
    <AlbayanLayout
      preview="دعوة للانضمام إلى مجلة البيان"
      siteUrl={SITE_URL}
      contactEmail={CONTACT_EMAIL}
      assetBaseUrl={ASSET_BASE_URL}
    >
      <Section
        className="email-content"
        style={{ padding: "28px 34px 10px", textAlign: "center" }}
      >
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
          دعوة للانضمام إلى مجلة البيان
        </Heading>
        <InfoPanel>
          يسر مجلة البيان دعوتكم، <strong>{RECIPIENT_NAME}</strong>، لإنشاء حساب في
          منصتها والمشاركة في بيئتها العلمية والإدارية.
          <br />
          أُرسلت هذه الدعوة إلى:
          <br />
          <span dir="ltr" style={{ overflowWrap: "anywhere" }}>
            {RECIPIENT_EMAIL}
          </span>
        </InfoPanel>
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
          استخدموا الزر الآتي لقبول الدعوة وإنشاء الحساب المرتبط بهذا
          البريد.
        </Text>
        <ActionButton href={INVITATION_URL}>
          قبول الدعوة وإنشاء الحساب
        </ActionButton>
        <Text
          style={{
            color: colors.muted,
            fontFamily,
            fontSize: "13px",
            lineHeight: "1.9",
            margin: "0 0 12px",
            textAlign: "center",
          }}
        >
          تنتهي صلاحية الدعوة في: {EXPIRES_TEXT}
        </Text>
      </Section>
    </AlbayanLayout>
  );
}

AppInvitationEmail.PreviewProps = {
  INVITATION_URL:
    "https://accounts.example/invitations/accept?__clerk_ticket=sample-ticket",
  RECIPIENT_NAME: "أحمد الزهراني",
  RECIPIENT_EMAIL: "person@example.com",
  EXPIRES_TEXT: "١٥ ربيع الأول ١٤٤٨ هـ",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies AppInvitationEmailProps;
