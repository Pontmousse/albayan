export const colors = {
  ink: "#17231c",
  muted: "#5b625c",
  border: "#e5dcc8",
  accent: "#1f5a46",
  accentStrong: "#123f33",
  gold: "#a67c1a",
  accentSoft: "#f4eee3",
  paper: "#fbf8f1",
  white: "#ffffff",
};

export const fontFamily =
  '"Noto Kufi Arabic", "Noto Sans Arabic", Tahoma, Arial, sans-serif';

export const displayFontFamily =
  'Amiri, "Noto Kufi Arabic", "Noto Sans Arabic", Tahoma, Arial, sans-serif';

export function resendTemplateVariable(name: string): string {
  if (!/^[A-Z0-9_]+$/.test(name)) {
    throw new Error(`Invalid Resend template variable: ${name}`);
  }
  return `{{{${name}}}}`;
}

/** Resend replaces this value after the template has been published. */
export const ASSET_BASE_URL_PLACEHOLDER =
  resendTemplateVariable("ASSET_BASE_URL");

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function isAllowedAssetBaseUrl(value: string): boolean {
  if (value === ASSET_BASE_URL_PLACEHOLDER) return true;

  try {
    const url = new URL(value);
    if (url.protocol === "https:") return true;
    return (
      url.protocol === "http:" &&
      ["localhost", "127.0.0.1", "[::1]", "::1"].includes(url.hostname)
    );
  } catch {
    return false;
  }
}

export function emailAssetUrl(
  assetBaseUrl: string | undefined,
  fileName: string,
): string {
  const baseUrl = assetBaseUrl?.trim();
  if (!baseUrl || !isAllowedAssetBaseUrl(baseUrl)) {
    throw new Error(
      "Email asset base URL must be the Resend placeholder, an absolute HTTPS URL, or a local preview URL.",
    );
  }

  const assetPath = fileName.replace(/^\/+/, "");
  if (!assetPath) throw new Error("Email asset path cannot be empty.");

  return `${normalizeBaseUrl(baseUrl)}/${assetPath}`;
}
