import Link from "next/link";
import type { PublicArticleSummary } from "@/lib/api/public";
import { PublishedArticlesSection } from "@/components/journal/published-articles-section";

type PublishedJournalHomeProps = {
  articles: PublicArticleSummary[];
};

/**
 * واجهة الرئيسية الغنية — تُفعَّل تلقائيًا عندما published_count &gt; 0 في API.
 * لا تُضاف ISSN أو DOI أو «العدد الحالي» هنا إلا عند توفر بيانات حقيقية.
 */
export function PublishedJournalHome({ articles }: PublishedJournalHomeProps) {
  return (
    <>
      <section className="border-b border-[var(--journal-border)] bg-[linear-gradient(180deg,var(--journal-accent-soft)_0%,var(--journal-paper)_100%)]">
        <div className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8 lg:py-14">
          <div className="mx-auto max-w-3xl space-y-5 text-center sm:space-y-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              منشورات المجلة
            </p>
            <h1
              className="text-balance text-2xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              مجلة علمية عربية للنشر الرصين والوصول الحر إلى المعرفة
            </h1>
            <p className="text-pretty text-sm leading-relaxed text-slate-600 sm:text-lg">
              تهدف «البيان» إلى دعم الباحثين والمؤسسات الأكاديمية عبر تحكيم أقران
              صارم، وسياسات نشر واضحة، وأرشفة دائمة للأبحاث المعتمدة.
            </p>
            <div className="flex flex-col items-stretch justify-center gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:gap-3">
              <Link
                href="/irshadat-al-mualifin"
                className="inline-flex min-h-11 items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
              >
                إرشادات المؤلفين
              </Link>
              <Link
                href="/siyasat-an-nashr"
                className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-[var(--journal-accent)]"
              >
                سياسة النشر
              </Link>
            </div>
          </div>
        </div>
      </section>

      <PublishedArticlesSection articles={articles} />
    </>
  );
}
