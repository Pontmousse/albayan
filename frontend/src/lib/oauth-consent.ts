/** Application-domain OAuth consent route (Clerk Dashboard Paths → this path). */
export const OAUTH_CONSENT_PATH = "/oauth-consent";

/** Human-readable Arabic labels for common OAuth scopes. */
const SCOPE_LABELS_AR: Record<string, string> = {
  openid: "معرّف الدخول المفتوح (OpenID)",
  profile: "الملف الشخصي الأساسي",
  email: "عنوان البريد الإلكتروني",
  offline_access: "البقاء متصلاً حتى تلغي الصلاحية",
  "public_metadata": "البيانات العامة لحسابك",
  "private_metadata": "البيانات الخاصة لحسابك",
};

export function scopeLabelAr(scope: string, description: string | null): string {
  const key = scope.trim();
  if (SCOPE_LABELS_AR[key]) return SCOPE_LABELS_AR[key];
  if (description?.trim()) return description.trim();
  return key;
}

/** Only allow http(s) image URLs from OAuth application metadata. */
export function safeHttpUrl(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    return url.toString();
  } catch {
    return null;
  }
}

export function redirectHostname(redirectUri: string): string {
  try {
    return new URL(redirectUri).hostname;
  } catch {
    return redirectUri;
  }
}
