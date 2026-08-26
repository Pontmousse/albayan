"use client";

import { useAuth, useClerk, useOAuthConsent, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { buttonClassName, translateClerkError } from "@/lib/auth-ui";
import {
  OAUTH_CONSENT_PATH,
  redirectHostname,
  safeHttpUrl,
  scopeLabelAr,
} from "@/lib/oauth-consent";

function signInHref(search: string): string {
  const next = `${OAUTH_CONSENT_PATH}${search}`;
  return `/tawajjuh?next=${encodeURIComponent(next)}`;
}

function SignedOutConsentPrompt() {
  const searchParams = useSearchParams();
  const search = searchParams.toString();
  const href = signInHref(search ? `?${search}` : "");

  return (
    <div className="oauth-consent-panel mx-auto w-full max-w-lg rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)]/95 p-6 shadow-[0_20px_60px_-28px_rgba(23,35,28,0.45)] sm:p-8">
      <p className="text-sm text-[var(--journal-muted)]">يلزم تسجيل الدخول</p>
      <h2
        className="mt-2 text-2xl font-bold text-[var(--journal-ink)]"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        أكمل التفويض بعد الدخول
      </h2>
      <p className="mt-3 text-sm leading-7 text-[var(--journal-muted)]">
        لعرض طلب الوصول والموافقة أو الرفض، سجّل دخولك إلى حسابك في البيان أولاً.
        ستُعاد إلى هذه الصفحة مع معاملات التفويض كما هي.
      </p>
      <Link href={href} className={`${buttonClassName} mt-6 w-full sm:w-auto`}>
        تسجيل الدخول
      </Link>
    </div>
  );
}

function ConsentDecisionForm() {
  const clerk = useClerk();
  const { user, isLoaded: userLoaded } = useUser();
  const { isLoaded: authLoaded } = useAuth();
  const searchParams = useSearchParams();
  const [showFullRedirect, setShowFullRedirect] = useState(false);

  const clientId = searchParams.get("client_id") ?? "";
  const redirectUri = searchParams.get("redirect_uri") ?? "";
  const scope = searchParams.get("scope") ?? undefined;

  const { data, isLoading, error } = useOAuthConsent({
    oauthClientId: clientId,
    scope,
    redirectUri: redirectUri || undefined,
    enabled: Boolean(clientId),
  });

  const logoUrl = useMemo(
    () => safeHttpUrl(data?.oauthApplicationLogoUrl),
    [data?.oauthApplicationLogoUrl],
  );

  const appUrl = useMemo(
    () => safeHttpUrl(data?.oauthApplicationUrl),
    [data?.oauthApplicationUrl],
  );

  const displayDomain =
    data?.redirectDomain || (redirectUri ? redirectHostname(redirectUri) : null);

  const identifier =
    user?.primaryEmailAddress?.emailAddress ??
    user?.username ??
    user?.fullName ??
    user?.id ??
    "حسابك";

  const consentActionUrl =
    clientId && clerk.oauthApplication
      ? clerk.oauthApplication.buildConsentActionUrl({ clientId })
      : "";

  const scopesRequiringConsent =
    data?.scopes.filter((item) => item.requiresConsent) ?? [];
  const scopesToShow =
    scopesRequiringConsent.length > 0 ? scopesRequiringConsent : (data?.scopes ?? []);

  if (!clientId || !redirectUri) {
    return (
      <div className="oauth-consent-panel mx-auto w-full max-w-lg rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)]/95 p-6 sm:p-8">
        <h2
          className="text-xl font-bold text-[var(--journal-ink)]"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          طلب تفويض غير مكتمل
        </h2>
        <p className="mt-3 text-sm leading-7 text-[var(--journal-muted)]">
          تنقص معاملات OAuth المطلوبة (`client_id` و`redirect_uri`). أعد الربط من
          تطبيق الوكيل (مثل ChatGPT) ولا تفتح هذه الصفحة يدوياً.
        </p>
      </div>
    );
  }

  if (!authLoaded || !userLoaded || isLoading) {
    return (
      <div
        className="oauth-consent-panel mx-auto flex w-full max-w-lg flex-col items-center gap-3 rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)]/95 p-10 text-center"
        aria-busy="true"
      >
        <span className="oauth-consent-pulse h-10 w-10 rounded-full border-2 border-[var(--journal-accent)] border-t-transparent" />
        <p className="text-sm text-[var(--journal-muted)]">جارٍ تحميل طلب التفويض…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="oauth-consent-panel mx-auto w-full max-w-lg rounded-2xl border border-red-200 bg-[var(--journal-paper)]/95 p-6 sm:p-8">
        <h2
          className="text-xl font-bold text-red-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          تعذّر تحميل طلب التفويض
        </h2>
        <p className="mt-3 text-sm leading-7 text-red-800" role="alert">
          {error ? translateClerkError(error) : "انتهت الجلسة أو لم يعد الطلب صالحاً."}
        </p>
        <p className="mt-3 text-sm text-[var(--journal-muted)]">
          سجّل الدخول مجدداً أو أعد محاولة الربط من تطبيق الوكيل.
        </p>
        <Link
          href={signInHref(`?${searchParams.toString()}`)}
          className={`${buttonClassName} mt-6`}
        >
          تسجيل الدخول مجدداً
        </Link>
      </div>
    );
  }

  const appName = data.oauthApplicationName || "تطبيق خارجي";

  return (
    <form
      method="POST"
      action={consentActionUrl}
      className="oauth-consent-panel mx-auto w-full max-w-lg rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)]/95 p-6 shadow-[0_20px_60px_-28px_rgba(23,35,28,0.45)] sm:p-8"
    >
      <div className="flex items-start gap-4">
        {logoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- remote OAuth client logo URL
          <img
            src={logoUrl}
            alt=""
            width={56}
            height={56}
            className="oauth-consent-logo h-14 w-14 shrink-0 rounded-xl border border-[var(--journal-border)] bg-white object-contain p-1.5"
          />
        ) : (
          <div
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-[var(--journal-border)] bg-[var(--journal-accent-soft)] text-lg font-bold text-[var(--journal-accent)]"
            aria-hidden
          >
            {appName.slice(0, 1)}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium tracking-wide text-[var(--journal-gold)]">
            طلب وصول إلى حسابك
          </p>
          <h2
            className="mt-1 text-2xl font-bold leading-snug text-[var(--journal-ink)]"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            <span className="text-[var(--journal-accent)]">{appName}</span>
            {" يريد الوصول إلى البيان"}
          </h2>
          <p className="mt-2 text-sm text-[var(--journal-muted)]">
            بالنيابة عن{" "}
            <span className="font-semibold text-[var(--journal-ink)]">{identifier}</span>
          </p>
        </div>
      </div>

      {appUrl ? (
        <p className="mt-4 text-xs text-[var(--journal-muted)]">
          موقع التطبيق:{" "}
          <a
            href={appUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-[var(--journal-accent)] underline-offset-2 hover:underline"
          >
            {appUrl}
          </a>
        </p>
      ) : null}

      <p className="mt-2 break-all text-xs text-[var(--journal-muted)]">
        معرّف العميل: <code className="font-mono text-[0.7rem]">{data.clientId}</code>
      </p>

      <div className="oauth-consent-warning mt-5 rounded-xl border border-[var(--journal-gold)]/35 bg-[var(--journal-accent-soft)]/80 px-4 py-3 text-sm leading-7 text-[var(--journal-ink)]">
        تأكد أنك تثق بـ{" "}
        <strong>{appName}</strong>
        {displayDomain ? (
          <>
            {" "}
            وأن الوجهة{" "}
            <strong dir="ltr" className="inline-block font-semibold">
              {displayDomain}
            </strong>{" "}
            صحيحة
          </>
        ) : null}
        . قد يُشارك التطبيق بيانات حساسة من حسابك في البيان.
      </div>

      <section className="mt-6" aria-labelledby="oauth-scopes-heading">
        <h3
          id="oauth-scopes-heading"
          className="text-sm font-semibold text-[var(--journal-ink)]"
        >
          سيُسمح لـ {appName} بالوصول إلى:
        </h3>
        <ul className="mt-3 space-y-2">
          {scopesToShow.map((item, index) => (
            <li
              key={`${item.scope}:${index}`}
              className="oauth-consent-scope flex items-start gap-3 rounded-lg border border-[var(--journal-border)] bg-white/70 px-3 py-2.5 text-sm"
              style={{ animationDelay: `${80 + index * 60}ms` }}
            >
              <span
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--journal-accent)]"
                aria-hidden
              />
              <span className="font-medium text-[var(--journal-ink)]">
                  {scopeLabelAr(item.scope, item.description)}
                </span>
            </li>
          ))}
        </ul>
      </section>

      {displayDomain || redirectUri ? (
        <div className="mt-5 text-sm text-[var(--journal-muted)]">
          <p>
            بعد الموافقة أو الرفض ستُعاد إلى{" "}
            <strong dir="ltr" className="text-[var(--journal-ink)]">
              {displayDomain || redirectHostname(redirectUri)}
            </strong>
            .
          </p>
          <button
            type="button"
            className="mt-2 text-xs font-semibold text-[var(--journal-accent)] underline-offset-2 hover:underline"
            onClick={() => setShowFullRedirect((v) => !v)}
            aria-expanded={showFullRedirect}
          >
            {showFullRedirect ? "إخفاء الرابط الكامل" : "عرض رابط الإعادة الكامل"}
          </button>
          {showFullRedirect ? (
            <p
              dir="ltr"
              className="mt-2 break-all rounded-md border border-[var(--journal-border)] bg-white/80 px-3 py-2 text-start font-mono text-[0.7rem] text-[var(--journal-ink)]"
            >
              {redirectUri}
            </p>
          ) : null}
        </div>
      ) : null}

      {/* Forward original OAuth params; never let query override consented / organization_id. */}
      {Array.from(searchParams.entries())
        .filter(([key]) => key !== "consented" && key !== "organization_id")
        .map(([key, value], index) => (
          <input key={`${key}:${index}`} type="hidden" name={key} value={value} />
        ))}

      <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          type="submit"
          name="consented"
          value="false"
          disabled={!consentActionUrl}
          className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 py-2.5 text-sm font-semibold text-[var(--journal-ink)] transition hover:border-[var(--journal-muted)] hover:bg-[var(--journal-accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          رفض
        </button>
        <button
          type="submit"
          name="consented"
          value="true"
          disabled={!consentActionUrl}
          className="inline-flex min-h-12 cursor-pointer items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          السماح
        </button>
      </div>

      <p className="mt-4 text-center text-xs text-[var(--journal-muted)]">
        البيان لا يعيد كتابة بروتوكول OAuth — الموافقة تُرسل إلى Clerk ثم يكتمل
        التفويض مع التطبيق الطالب.
      </p>
    </form>
  );
}

export function OAuthConsentExperience() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <div
        className="oauth-consent-panel mx-auto flex w-full max-w-lg flex-col items-center gap-3 rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)]/95 p-10 text-center"
        aria-busy="true"
      >
        <span className="oauth-consent-pulse h-10 w-10 rounded-full border-2 border-[var(--journal-accent)] border-t-transparent" />
        <p className="text-sm text-[var(--journal-muted)]">جارٍ التحقق من الجلسة…</p>
      </div>
    );
  }

  if (!isSignedIn) {
    return <SignedOutConsentPrompt />;
  }

  return <ConsentDecisionForm />;
}
