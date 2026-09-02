"use client";

import { useNumerals } from "@/components/numeral-provider";
import { formatPublicAuthors, type PublicArticleSummary } from "@/lib/api/public";

type ArticleCardProps = {
  article: PublicArticleSummary;
};

/** بطاقة مقال منشور — بدون روابط وهمية أو DOI/ISSN مختلقة. */
export function ArticleCard({ article }: ArticleCardProps) {
  const { formatDate } = useNumerals();
  return (
    <article className="flex flex-col rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
      <div className="mb-3 text-xs text-slate-500">
        <time dateTime={article.published_at}>{formatDate(article.published_at)}</time>
      </div>
      <h3
        className="text-lg font-bold leading-snug text-slate-900"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {article.title}
      </h3>
      <p className="mt-2 text-sm font-medium text-slate-700">
        {formatPublicAuthors(article.authors)}
      </p>
      {article.abstract ? (
        <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-slate-600">
          {article.abstract}
        </p>
      ) : null}
    </article>
  );
}
