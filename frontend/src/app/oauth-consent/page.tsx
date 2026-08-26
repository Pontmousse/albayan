import { Suspense } from "react";
import { OAuthConsentExperience } from "@/components/oauth/oauth-consent-form";

function ConsentFallback() {
  return (
    <div
      className="flex flex-1 flex-col items-center justify-center px-4 py-16 text-sm text-[var(--journal-muted)]"
      aria-busy="true"
    >
      جارٍ التحميل…
    </div>
  );
}

export default function OAuthConsentPage() {
  return (
    <div className="oauth-consent-page relative flex min-h-screen flex-1 flex-col overflow-hidden">
      <div className="oauth-consent-atmosphere pointer-events-none absolute inset-0" aria-hidden />

      <header className="oauth-consent-brand relative z-10 px-4 pb-2 pt-10 text-center sm:pt-14">
        <p
          className="text-4xl font-bold tracking-tight text-[var(--journal-accent)] sm:text-5xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          البيان
        </p>
        <p className="mt-2 text-sm text-[var(--journal-muted)]">مجلة علمية محكّمة</p>
        <p className="mx-auto mt-4 max-w-md text-sm leading-7 text-[var(--journal-ink)]/80">
          تفويض آمن لربط وكيل ذكي بحسابك — أنت من يقرر السماح أو الرفض.
        </p>
      </header>

      <main className="relative z-10 flex flex-1 flex-col justify-center px-4 pb-14 pt-6 sm:px-6">
        <Suspense fallback={<ConsentFallback />}>
          <OAuthConsentExperience />
        </Suspense>
      </main>
    </div>
  );
}
