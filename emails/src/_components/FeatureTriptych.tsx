import * as React from "react";
import { Img, Section, Text } from "react-email";
import { colors, displayFontFamily, emailAssetUrl, fontFamily } from "./theme";

type Feature = {
  imageFileName: string;
  title: string;
  body: string;
};

type FeatureTriptychProps = {
  features: [Feature, Feature, Feature];
  assetBaseUrl?: string;
};

export function FeatureTriptych({ features, assetBaseUrl }: FeatureTriptychProps) {
  return (
    <Section
      style={{
        backgroundColor: "#fffdf8",
        border: `1px solid ${colors.border}`,
        borderRadius: "14px",
        margin: "26px 0",
        padding: "20px 10px",
      }}
    >
      <table role="presentation" width="100%" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr>
            {features.map((feature) => (
              <td
                key={feature.title}
                align="center"
                valign="top"
                width="33.333%"
                style={{
                  padding: "4px 12px",
                }}
              >
                <Img
                  src={emailAssetUrl(assetBaseUrl, feature.imageFileName)}
                  alt=""
                  width="64"
                  height="64"
                  style={{
                    display: "block",
                    height: "64px",
                    margin: "0 auto 12px",
                    objectFit: "contain",
                    width: "64px",
                  }}
                />
                <Text
                  style={{
                    color: colors.accentStrong,
                    fontFamily: displayFontFamily,
                    fontSize: "17px",
                    fontWeight: 700,
                    lineHeight: "1.5",
                    margin: "0 0 5px",
                    textAlign: "center",
                  }}
                >
                  {feature.title}
                </Text>
                <Text
                  style={{
                    color: colors.ink,
                    fontFamily,
                    fontSize: "13px",
                    lineHeight: "1.75",
                    margin: 0,
                    textAlign: "center",
                  }}
                >
                  {feature.body}
                </Text>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </Section>
  );
}
