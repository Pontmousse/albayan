import * as React from "react";
import { Heading, Link, Section, Text } from "react-email";
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
  RECIPIENT_EMAIL?: string;
  EXPIRES_TEXT?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function AppInvitationEmail({
  INVITATION_URL = resendTemplateVariable("INVITATION_URL"),
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
        <GoldDivider spacing={22} assetBaseUrl={ASSET_BASE_URL} />
        <Heading
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
          دُعي هذا البريد، {RECIPIENT_EMAIL}، لإنشاء حساب في منصة مجلة البيان
          والمشاركة في بيئتها العلمية والإدارية.
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
          يرجى استخدام الرابط الآمن الآتي لقبول الدعوة وإنشاء الحساب. ستتولى
          Clerk التحقق من الدعوة وربطها بهذا البريد.
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
            href={INVITATION_URL}
            style={{
              color: colors.accent,
              fontFamily,
              textDecoration: "underline",
            }}
          >
            {INVITATION_URL}
          </Link>
        </Text>
      </Section>
    </AlbayanLayout>
  );
}

AppInvitationEmail.PreviewProps = {
  INVITATION_URL:
    "https://accounts.example/invitations/accept?__clerk_ticket=sample-ticket",
  RECIPIENT_EMAIL: "person@example.com",
  EXPIRES_TEXT: "١٥ ربيع الأول ١٤٤٨ هـ",
  SITE_URL: "https://albayan-journal.org",
  CONTACT_EMAIL: "support@albayan-journal.org",
  ASSET_BASE_URL: "http://localhost:3001/static",
} satisfies AppInvitationEmailProps;
