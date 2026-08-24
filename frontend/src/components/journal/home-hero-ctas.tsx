"use client";

import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import type { ReactNode } from "react";
import { TUTORIALS_HREF, TUTORIALS_LABEL } from "@/lib/tutorials";

const primaryClassName =
  "inline-flex min-h-11 items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]";

const secondaryClassName =
  "inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-[var(--journal-accent)]";

const mcpClassName =
  "inline-flex min-h-11 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 px-5 text-sm font-semibold text-emerald-900 transition hover:border-emerald-300";

type HomeHeroCtasProps = {
  variant: "early" | "published";
  mcpEnabled: boolean;
  /** من `auth()` في الخادم لتفادي وميض أزرار الدخول قبل تحميل Clerk في المتصفح. */
  initialSignedIn: boolean;
};

function CtaLink({
  href,
  className,
  children,
}: {
  href: string;
  className: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  );
}

function McpCta() {
  return (
    <CtaLink href="/wukala" className={mcpClassName}>
      الوكلاء الذكيون
    </CtaLink>
  );
}

/**
 * أزرار دعوة الرئيسية حسب الجلسة.
 * الصفحة تبقى مكوّن خادم؛ هذه جزيرة عميل لأن ظهور «تسجيل الدخول»/«إنشاء حساب»
 * يجب أن يختفي للمسجّل ويُستبدل بمسارات حقيقية (`/maktabi` والسياسات والشروح).
 */
export function HomeHeroCtas({
  variant,
  mcpEnabled,
  initialSignedIn,
}: HomeHeroCtasProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const signedIn = isLoaded ? Boolean(isSignedIn) : initialSignedIn;

  if (signedIn) {
    return (
      <div className="flex flex-col items-stretch justify-center gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:gap-3">
        <CtaLink href="/maktabi" className={primaryClassName}>
          مكتبي
        </CtaLink>
        <CtaLink href={TUTORIALS_HREF} className={secondaryClassName}>
          {TUTORIALS_LABEL}
        </CtaLink>
        <CtaLink href="/siyasat-an-nashr" className={secondaryClassName}>
          سياسة النشر
        </CtaLink>
        <CtaLink href="/irshadat-al-mualifin" className={secondaryClassName}>
          إرشادات المؤلفين
        </CtaLink>
        {mcpEnabled ? <McpCta /> : null}
      </div>
    );
  }

  if (variant === "published") {
    return (
      <div className="flex flex-col items-stretch justify-center gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:gap-3">
        <CtaLink href="/irshadat-al-mualifin" className={primaryClassName}>
          إرشادات المؤلفين
        </CtaLink>
        <CtaLink href="/siyasat-an-nashr" className={secondaryClassName}>
          سياسة النشر
        </CtaLink>
        <CtaLink href={TUTORIALS_HREF} className={secondaryClassName}>
          {TUTORIALS_LABEL}
        </CtaLink>
        {mcpEnabled ? <McpCta /> : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-stretch justify-center gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:gap-3">
      <CtaLink href="/irshadat-al-mualifin" className={primaryClassName}>
        إرشادات المؤلفين
      </CtaLink>
      <CtaLink href="/tasjil" className={secondaryClassName}>
        إنشاء حساب
      </CtaLink>
      <CtaLink href="/tawajjuh" className={secondaryClassName}>
        تسجيل الدخول
      </CtaLink>
      <CtaLink href={TUTORIALS_HREF} className={secondaryClassName}>
        {TUTORIALS_LABEL}
      </CtaLink>
      {mcpEnabled ? <McpCta /> : null}
    </div>
  );
}
