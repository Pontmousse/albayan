import Image from "next/image";
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

      <header className="oauth-consent-brand relative z-10 px-4 pb-1 pt-6 text-center sm:pt-10">
        <Image
          src="/albayan.svg"
          alt="شعار مجلة البيان"
          width={80}
          height={80}
          priority
          className="mx-auto h-16 w-16 rounded-2xl object-contain shadow-sm sm:h-20 sm:w-20"
        />
        <p
          className="mt-2 text-2xl font-bold tracking-tight text-[var(--journal-accent)] sm:text-3xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          البيان
        </p>
        <p className="mt-1 text-sm text-[var(--journal-muted)]">مجلة علمية محكّمة</p>
        <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-[var(--journal-ink)]/80">
          تفويض آمن لربط وكيل ذكي بحسابك — أنت من يقرر السماح أو الرفض.
        </p>
      </header>

      <main className="relative z-10 flex flex-1 flex-col justify-center px-4 pb-10 pt-4 sm:px-6 sm:pb-14 sm:pt-6">
        <Suspense fallback={<ConsentFallback />}>
          <OAuthConsentExperience />
        </Suspense>
      </main>
    </div>
  );
}
