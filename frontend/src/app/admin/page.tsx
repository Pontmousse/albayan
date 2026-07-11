"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useEffect, useState } from "react";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import {
  listAdminArticles,
  type AdminArticleSummary,
} from "@/lib/api/admin";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

function SummaryCard({
  label,
  value,
  index,
}: {
  label: string;
  value: number;
  index: number;
}) {
  return (
    <div
      className="stagger-item rounded-xl border border-amber-200 bg-white/80 p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
      style={{ "--stagger-index": index } as React.CSSProperties}
    >
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p
        className="mt-2 text-3xl font-bold text-[var(--journal-accent-strong)]"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {value}
      </p>
    </div>
  );
}

export default function AdminOverviewPage() {
  const { getToken } = useAuth();
  const [articles, setArticles] = useState<AdminArticleSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAdminArticles(getToken)
      .then((data) => {
        if (!cancelled) setArticles(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل البيانات.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const drafts = articles?.filter((a) => a.status === "draft").length ?? 0;
  const inFlight =
    articles?.filter(
      (a) => a.status === "submitted" || a.status === "under_review",
    ).length ?? 0;
  const accepted = articles?.filter((a) => a.status === "accepted").length ?? 0;
  const rejected = articles?.filter((a) => a.status === "rejected").length ?? 0;
  const recent = articles?.slice(0, 5) ?? [];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            نظرة عامة
          </h1>
          <p className="mt-1.5 text-sm text-slate-600">
            ملخص سريع للمقالات والتعيينات في المجلة.
          </p>
        </div>
        <Link href="/admin/maqalat" className={buttonClassName}>
          كل المقالات
        </Link>
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : articles === null ? (
        <>
          <CardsSkeleton />
          <RowsSkeleton />
        </>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard label="مسودات" value={drafts} index={0} />
            <SummaryCard label="قيد المعالجة" value={inFlight} index={1} />
            <SummaryCard label="مقبولة" value={accepted} index={2} />
            <SummaryCard label="مرفوضة" value={rejected} index={3} />
          </div>

          <section>
            <div className="flex items-center justify-between">
              <h2
                className="text-lg font-bold text-[var(--journal-accent)]"
                style={{ fontFamily: "var(--font-display-ar), serif" }}
              >
                آخر المقالات
              </h2>
              <Link
                href="/admin/maqalat"
                className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
              >
                عرض الكل
              </Link>
            </div>
            {recent.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">لا مقالات بعد.</p>
            ) : (
              <ul className="mt-3 space-y-2.5">
                {recent.map((article, index) => (
                  <li
                    key={article.id}
                    className="stagger-item"
                    style={
                      { "--stagger-index": index + 4 } as React.CSSProperties
                    }
                  >
                    <Link
                      href={`/admin/maqalat/${article.id}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md"
                    >
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-800">
                        {article.title}
                      </span>
                      <span className="flex shrink-0 items-center gap-3">
                        <StatusBadge status={article.status} />
                        <span className="text-xs text-slate-500">
                          {formatDate(article.updated_at)}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
