import * as React from "react";
import { Img, Section } from "react-email";
import { colors, emailAssetUrl } from "./theme";

type AlbayanHeaderProps = {
  assetBaseUrl?: string;
};

export function AlbayanHeader({ assetBaseUrl }: AlbayanHeaderProps) {
  const logoUrl = emailAssetUrl(assetBaseUrl, "logo.png");
  const archUrl = emailAssetUrl(assetBaseUrl, "header-arch.png");

  return (
    <Section
      style={{
        backgroundColor: colors.accentSoft,
        backgroundImage: archUrl ? `url(${archUrl})` : undefined,
        backgroundPosition: "top center",
        backgroundRepeat: "no-repeat",
        backgroundSize: "124% auto",
        borderBottom: `1px solid ${colors.border}`,
        padding: "296px 32px 34px",
        textAlign: "center",
      }}
    >
      <Img
        src={logoUrl}
        alt="مجلة البيان"
        width="370"
        height="148"
        style={{
          display: "block",
          height: "auto",
          margin: "0 auto",
          maxWidth: "370px",
          objectFit: "contain",
          width: "90%",
        }}
      />
    </Section>
  );
}
