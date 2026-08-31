import * as React from "react";
import { Img, Section } from "react-email";
import { colors, emailAssetUrl } from "./theme";

type GoldDividerProps = {
  spacing?: number;
  assetBaseUrl?: string;
};

export function GoldDivider({ spacing = 24, assetBaseUrl }: GoldDividerProps) {
  return (
    <Section style={{ padding: `${spacing}px 0` }}>
      <Img
        src={emailAssetUrl(assetBaseUrl, "divider.png")}
        alt=""
        width="260"
        height="87"
        style={{
          display: "block",
          height: "auto",
          margin: "0 auto",
          maxWidth: "260px",
          width: "72%",
        }}
      />
      <div style={{ borderTop: `1px solid ${colors.border}`, height: 0 }} />
    </Section>
  );
}
