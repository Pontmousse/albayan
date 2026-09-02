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
  return (
    <Section
      style={{
        backgroundColor: "#f3eee4",
        borderTop: `1px solid ${colors.border}`,
        padding: "22px 0 18px",
        textAlign: "center",
      }}
    >
      <table
        role="presentation"
        width="100%"
        cellPadding="0"
        cellSpacing="0"
        dir="ltr"
      >
        <tbody>
          <tr>
            <td
              align="right"
              valign="middle"
              width="18%"
              className="email-footer-corner-cell"
              style={{ padding: "172px 0 0 8px" }}
            >
              <Img
                src={emailAssetUrl(assetBaseUrl, "footer-corner-left.png")}
                alt=""
                width="72"
                height="72"
                className="email-fluid-image"
                style={{
                  display: "block",
                  height: "auto",
                  maxWidth: "104px",
                  objectFit: "contain",
                  width: "100%",
                }}
              />
            </td>
            <td
              align="center"
              valign="middle"
              width="64%"
              dir="rtl"
              className="email-footer-center-cell"
              style={{ padding: "0 4px" }}
            >
              <table role="presentation" cellPadding="0" cellSpacing="0" align="center">
                <tbody>
                  <tr>
                    <td align="center" style={{ padding: "0 7px 14px" }}>
                      <Link
                        href={siteUrl}
                        aria-label="زيارة موقع مجلة البيان"
                        style={{
                          display: "block",
                          textDecoration: "none",
                        }}
                      >
                        <Img
                          src={emailAssetUrl(assetBaseUrl, "icons/website.png")}
                          alt=""
                          width="30"
                          height="30"
                          style={{
                            display: "block",
                            height: "30px",
                            margin: "0 auto",
                            objectFit: "contain",
                            width: "30px",
                          }}
                        />
                      </Link>
                    </td>
                    <td align="center" style={{ padding: "0 7px 14px" }}>
                      <Link
                        href={`mailto:${contactEmail}`}
                        aria-label="مراسلة مجلة البيان"
                        style={{
                          display: "block",
                          textDecoration: "none",
                        }}
                      >
                        <Img
                          src={emailAssetUrl(assetBaseUrl, "icons/email.png")}
                          alt=""
                          width="30"
                          height="30"
                          style={{
                            display: "block",
                            height: "30px",
                            margin: "0 auto",
                            objectFit: "contain",
                            width: "30px",
                          }}
                        />
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
              width="18%"
              className="email-footer-corner-cell"
              style={{ padding: "172px 8px 0 0" }}
            >
              <Img
                src={emailAssetUrl(assetBaseUrl, "footer-corner-right.png")}
                alt=""
                width="72"
                height="72"
                className="email-fluid-image"
                style={{
                  display: "block",
                  height: "auto",
                  maxWidth: "104px",
                  objectFit: "contain",
                  width: "100%",
                }}
              />
            </td>
          </tr>
        </tbody>
      </table>
    </Section>
  );
}
