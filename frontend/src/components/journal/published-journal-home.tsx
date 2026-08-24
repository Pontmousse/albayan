import type { PublicArticleSummary } from "@/lib/api/public";
import { HomeHeroCtas } from "@/components/journal/home-hero-ctas";
import { PublishedArticlesSection } from "@/components/journal/published-articles-section";
import { isMcpEnabled } from "@/lib/mcp-enabled";

type PublishedJournalHomeProps = {
  articles: PublicArticleSummary[];
  signedIn: boolean;
};

/**
 * واجهة الرئيسية الغنية — تُفعَّل تلقائيًا عندما published_count &gt; 0 في API.
 * لا تُضاف ISSN أو DOI أو «العدد الحالي» هنا إلا عند توفر بيانات حقيقية.
 */
export function PublishedJournalHome({
  articles,
  signedIn,
}: PublishedJournalHomeProps) {
  const mcpEnabled = isMcpEnabled();
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
            <HomeHeroCtas
              variant="published"
              mcpEnabled={mcpEnabled}
              initialSignedIn={signedIn}
            />
          </div>
        </div>
      </section>

      <PublishedArticlesSection articles={articles} />
    </>
  );
}
