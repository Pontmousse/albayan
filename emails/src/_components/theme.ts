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

export function emailAssetUrl(
  assetBaseUrl: string | undefined,
  fileName: string,
): string {
  const normalizedAssetBaseUrl = assetBaseUrl?.replace(/\/$/, "");
  return normalizedAssetBaseUrl
    ? `${normalizedAssetBaseUrl}/${fileName}`
    : `/static/${fileName}`;
}
