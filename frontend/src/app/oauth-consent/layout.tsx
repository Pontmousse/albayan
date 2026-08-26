import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "تفويض الوصول | البيان",
  description:
    "مراجعة طلب وصول تطبيق خارجي إلى حسابك في مجلة البيان والموافقة أو الرفض.",
  referrer: "strict-origin-when-cross-origin",
  robots: { index: false, follow: false },
};

/**
 * Minimal consent shell: no journal header/footer (handled by AppChrome).
 * Referrer policy is required so Clerk's FAPI consent POST includes Origin.
 */
export default function OAuthConsentLayout({ children }: { children: ReactNode }) {
  return children;
}
