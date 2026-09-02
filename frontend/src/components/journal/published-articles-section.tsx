"use client";

import type { PublicArticleSummary } from "@/lib/api/public";
import { ArticleCard } from "@/components/journal/article-card";
import { useNumerals } from "@/components/numeral-provider";

type PublishedArticlesSectionProps = {
  articles: PublicArticleSummary[];
};

/** قائمة المقالات المنشورة من API — تُعرض فقط عندما published_count &gt; 0. */
export function PublishedArticlesSection({ articles }: PublishedArticlesSectionProps) {
  const { formatNumber } = useNumerals();
  return (
    <section className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8">
      <div className="mb-8 space-y-2">
        <h2
          className="text-2xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          المقالات المنشورة
        </h2>
        <p className="text-sm text-slate-600">
          {articles.length === 1
            ? "مقال واحد منشور حاليًا."
            : `${formatNumber(articles.length)} مقالات منشورة حاليًا.`}
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>
    </section>
  );
}
