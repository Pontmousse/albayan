import * as React from "react";
import { Img, Link, Section, Text } from "react-email";
import { colors, emailAssetUrl, fontFamily } from "./theme";

type AlbayanFooterProps = {
  siteUrl: string;
  contactEmail: string;
  assetBaseUrl?: string;
};

export function AlbayanFooter({
  siteUrl,
  contactEmail,
  assetBaseUrl,
}: AlbayanFooterProps) {
  const displayUrl = siteUrl.replace(/^https?:\/\//, "");

  return (
    <Section
      style={{
        backgroundColor: "#f3eee4",
        borderTop: `1px solid ${colors.border}`,
        padding: "22px 0 18px",
        textAlign: "center",
      }}
    >
      <table role="presentation" width="100%" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr>
            <td
              align="right"
              valign="middle"
              width="118"
              style={{ padding: "64px 26px 0 0" }}
            >
              <Img
                src={emailAssetUrl(assetBaseUrl, "corner-ornament-footer.png")}
                alt=""
                width="104"
                height="104"
                style={{
                  display: "block",
                  height: "104px",
                  objectFit: "contain",
                  transform: "scaleX(-1)",
                  width: "104px",
                }}
              />
            </td>
            <td align="center" valign="middle" style={{ padding: "0 4px" }}>
              <table role="presentation" cellPadding="0" cellSpacing="0" align="center">
                <tbody>
                  <tr>
                    <td align="center" style={{ padding: "0 10px 12px" }}>
                      <Link
                        href={siteUrl}
                        style={{
                          color: colors.accent,
                          fontFamily,
                          fontSize: "13px",
                          fontWeight: 700,
                          textDecoration: "none",
                        }}
                      >
                        <Img
                          src={emailAssetUrl(assetBaseUrl, "icon-website.png")}
                          alt=""
                          width="30"
                          height="30"
                          style={{
                            display: "block",
                            height: "30px",
                            margin: "0 auto 6px",
                            objectFit: "contain",
                            width: "30px",
                          }}
                        />
                        {displayUrl}
                      </Link>
                    </td>
                    <td align="center" style={{ padding: "0 10px 12px" }}>
                      <Link
                        href={`mailto:${contactEmail}`}
                        style={{
                          color: colors.accent,
                          fontFamily,
                          fontSize: "13px",
                          fontWeight: 700,
                          textDecoration: "none",
                        }}
                      >
                        <Img
                          src={emailAssetUrl(assetBaseUrl, "icon-email.png")}
                          alt=""
                          width="30"
                          height="30"
                          style={{
                            display: "block",
                            height: "30px",
                            margin: "0 auto 6px",
                            objectFit: "contain",
                            width: "30px",
                          }}
                        />
                        {contactEmail}
                      </Link>
                    </td>
                  </tr>
                </tbody>
              </table>
              <Text
                style={{
                  color: colors.accentStrong,
                  fontFamily,
                  fontSize: "14px",
                  fontWeight: 700,
                  lineHeight: "1.8",
                  margin: "0 0 8px",
                  textAlign: "center",
                }}
              >
                مجلة البيان
              </Text>
              <Text
                style={{
                  color: colors.muted,
                  fontFamily,
                  fontSize: "12px",
                  lineHeight: "1.8",
                  margin: "0",
                  textAlign: "center",
                }}
              >
                أُرسلت هذه الرسالة لأنها مرتبطة بحسابكم أو أعمالكم العلمية في
                منصة البيان.
              </Text>
            </td>
            <td
              align="left"
              valign="middle"
              width="118"
              style={{ padding: "64px 0 0 26px" }}
            >
              <Img
                src={emailAssetUrl(assetBaseUrl, "corner-ornament-footer.png")}
                alt=""
                width="104"
                height="104"
                style={{
                  display: "block",
                  height: "104px",
                  objectFit: "contain",
                  width: "104px",
                }}
              />
            </td>
          </tr>
        </tbody>
      </table>
    </Section>
  );
}
