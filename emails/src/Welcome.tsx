import * as React from "react";
import { Heading, Section, Text } from "react-email";
import { ActionButton } from "./_components/ActionButton";
import { AlbayanLayout } from "./_components/AlbayanLayout";
import { FeatureTriptych } from "./_components/FeatureTriptych";
import { GoldDivider } from "./_components/GoldDivider";
import { InfoPanel } from "./_components/InfoPanel";
import { colors, displayFontFamily, fontFamily } from "./_components/theme";

type WelcomeEmailProps = {
  USER_NAME?: string;
  LOGIN_URL?: string;
  SITE_URL?: string;
  CONTACT_EMAIL?: string;
  ASSET_BASE_URL?: string;
};

export default function WelcomeEmail({
  USER_NAME = "الباحث الكريم",
  LOGIN_URL = "https://albayan-journal.org/maktabi",
  SITE_URL = "https://albayan-journal.org",
  CONTACT_EMAIL = "contact@albayan-journal.org",
  ASSET_BASE_URL,
}: WelcomeEmailProps) {
  return (
    <AlbayanLayout
      preview="مجلة البيان ترحب بكم"
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
          بسم الله الرحمن الرحيم، والصلاة والسلام على رسول الله صلى الله عليه وسلم
        </Text>
        <GoldDivider spacing={22} assetBaseUrl={ASSET_BASE_URL} />
        <Heading
          as="h1"
          style={{
            color: colors.accentStrong,
            fontFamily: displayFontFamily,
            fontSize: "34px",
            fontWeight: 700,
            lineHeight: "1.45",
            margin: "0",
            textAlign: "center",
          }}
        >
          مجلة البيان ترحب بكم
        </Heading>
        <Text
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "17px",
            lineHeight: "2",
            margin: "22px 0 0",
            textAlign: "center",
          }}
        >
          السلام عليكم ورحمة الله وبركاته
        </Text>
        <InfoPanel>
          أهلًا وسهلًا بكم، {USER_NAME}. يسعدنا انضمامكم إلى مجتمع مجلة البيان
          العلمي؛ فضاء محكّم للنشر الأكاديمي الجاد، يرحب بالبحث الرصين في
          مجالات المعرفة النافعة والعلوم الأصيلة والتطبيقية.
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
          نؤمن أن النظر العلمي الدقيق باب من أبواب الفهم والشكر، وأن خدمة
          الإنسان وعمارة الأرض تبدأ بمعرفة صادقة ومنهج أمين.
        </Text>
        <FeatureTriptych
          assetBaseUrl={ASSET_BASE_URL}
          features={[
            {
              imageFileName: "publish.png",
              title: "انشر بحثك",
              body: "قدّم أعمالك العلمية في بيئة أكاديمية تقدّر الدقة والمنهج.",
            },
            {
              imageFileName: "read.png",
              title: "اطلع وتعلّم",
              body: "تابع معرفة محكّمة تمتد عبر مجالات العلم والبحث الجاد.",
            },
            {
              imageFileName: "community.png",
              title: "تواصل وانضم",
              body: "كن جزءًا من مجتمع يطلب التميز والأمانة والمعرفة النافعة.",
            },
          ]}
        />
        <ActionButton href={LOGIN_URL}>الدخول إلى حسابكم</ActionButton>
        <Text
          style={{
            color: colors.ink,
            fontFamily,
            fontSize: "16px",
            lineHeight: "2",
            margin: "6px 0 0",
            textAlign: "center",
          }}
        >
          نشكركم على ثقتكم، ونتطلع إلى إسهاماتكم العلمية القيّمة.
        </Text>
        <Text
          style={{
            color: colors.accentStrong,
            fontFamily: displayFontFamily,
            fontSize: "18px",
            fontWeight: 700,
            lineHeight: "1.8",
            margin: "18px 0 0",
            textAlign: "center",
          }}
        >
          مع خالص التحية والتقدير
          <br />
          أسرة مجلة البيان
        </Text>
      </Section>
    </AlbayanLayout>
  );
}
