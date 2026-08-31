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

/** Resend replaces this with the absolute value passed in template variables. */
export const ASSET_BASE_URL_PLACEHOLDER = "{{{ASSET_BASE_URL}}}";

type EmailAssetUrlOptions = {
  /**
   * An explicit base URL used only by local preview tooling. This is allowed to
   * use HTTP so React Email can serve images from localhost.
   */
  previewBaseUrl?: string;
};

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function isAbsoluteUrl(value: string, protocol: "https:" | "http:"): boolean {
  try {
    return new URL(value).protocol === protocol;
  } catch {
    return false;
  }
}

export function emailAssetUrl(
  assetBaseUrl: string | undefined,
  fileName: string,
  options: EmailAssetUrlOptions = {},
): string {
  const publicBaseUrl = assetBaseUrl?.trim();

  if (publicBaseUrl) {
    if (
      publicBaseUrl !== ASSET_BASE_URL_PLACEHOLDER &&
      !isAbsoluteUrl(publicBaseUrl, "https:")
    ) {
      throw new Error(
        "Email asset base URL must be the ASSET_BASE_URL placeholder or an absolute HTTPS URL.",
      );
    }

    return `${normalizeBaseUrl(publicBaseUrl)}/${fileName}`;
  }

  const previewBaseUrl = options.previewBaseUrl?.trim();
  if (previewBaseUrl) {
    if (
      !isAbsoluteUrl(previewBaseUrl, "http:") &&
      !isAbsoluteUrl(previewBaseUrl, "https:")
    ) {
      throw new Error("Preview asset base URL must be an absolute URL.");
    }

    return `${normalizeBaseUrl(previewBaseUrl)}/${fileName}`;
  }

  throw new Error(
    "Email assets require a public ASSET_BASE_URL or an explicit previewBaseUrl.",
  );
}
