"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import {
  deleteArticle,
  listMyArticles,
  type ArticleSummary,
  type VersionStatus,
} from "@/lib/api/articles";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

type Filter = "all" | "draft" | "submitted" | "under_review" | "finished";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "الكل" },
  { id: "draft", label: "مسودات" },
  { id: "submitted", label: "مُقدَّمة" },
  { id: "under_review", label: "قيد المراجعة" },
  { id: "finished", label: "منتهية" },
];

const FINISHED: VersionStatus[] = ["accepted", "rejected", "published"];

const DELETE_CONFIRM =
  "حذف هذه المسودة نهائياً مع المخطوطة والصور وملف المعاينة؟ لا يمكن التراجع.";

function matchesFilter(article: ArticleSummary, filter: Filter): boolean {
  if (filter === "all") return true;
  if (filter === "finished") return FINISHED.includes(article.status);
  return article.status === filter;
}

export default function MaqalatiPage() {
  const { getToken } = useAuth();
  const [articles, setArticles] = useState<ArticleSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [pendingDelete, setPendingDelete] = useState<ArticleSummary | null>(
    null,
  );
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(() => {
    return listMyArticles(getToken)
      .then((data) => {
        setArticles(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "تعذّر تحميل المقالات.");
      });
  }, [getToken]);

  useEffect(() => {
    let cancelled = false;
    listMyArticles(getToken)
      .then((data) => {
        if (!cancelled) setArticles(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل المقالات.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  async function handleConfirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteArticle(getToken, pendingDelete.id);
      setPendingDelete(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر حذف المسودة.");
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  }

  const filtered = articles?.filter((a) => matchesFilter(a, filter)) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            مقالاتي
          </h1>
          <p className="mt-1.5 text-sm text-slate-600">
            جميع مخطوطاتك — من المسودة حتى النشر.
          </p>
        </div>
        <Link href="/maktabi/maqalati/jadid" className={buttonClassName}>
          مقال جديد
        </Link>
      </div>

      <div
        role="tablist"
        aria-label="تصفية حسب الحالة"
        className="flex flex-wrap gap-1.5"
      >
        {FILTERS.map((item) => {
          const activeTab = filter === item.id;
          return (
            <button
              key={item.id}
              role="tab"
              aria-selected={activeTab}
              onClick={() => setFilter(item.id)}
              className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-all duration-200 ${
                activeTab
                  ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white shadow-sm"
                  : "border-[var(--journal-border)] bg-white/70 text-slate-600 hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {articles === null && !error ? (
        <RowsSkeleton count={5} />
      ) : articles !== null && articles.length === 0 ? (
        <EmptyState
          title="لا مقالات بعد"
          description="ابدأ رحلتك في النشر العلمي — أنشئ مقالك الأول وحرّره عبر محرر البيان."
          actionLabel="ابدأ مقالك الأول"
          actionHref="/maktabi/maqalati/jadid"
        />
      ) : articles !== null && filtered.length === 0 ? (
        <EmptyState
          title="لا نتائج لهذا الفلتر"
          description="جرّب فلتراً آخر، أو أنشئ مقالاً جديداً."
        />
      ) : articles !== null ? (
        <ul className="space-y-2.5">
          {filtered.map((article, index) => (
            <li
              key={article.id}
              className="stagger-item"
              style={{ "--stagger-index": index } as React.CSSProperties}
            >
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md">
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/maktabi/maqalati/${article.id}`}
                    className="block truncate text-sm font-semibold text-slate-800 hover:text-[var(--journal-accent-strong)]"
                  >
                    {article.title}
                  </Link>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>الإصدار v{article.version_number}</span>
                    <span aria-hidden>·</span>
                    <span>آخر تحديث: {formatDate(article.updated_at)}</span>
                  </p>
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2 sm:gap-3">
                  <StatusBadge status={article.status} />
                  {article.status === "draft" ? (
                    <>
                      <Link
                        href={`/maktabi/maqalati/${article.id}/tahrir`}
                        className="rounded-md border border-[var(--journal-accent)] px-3 py-1.5 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent)] hover:text-white"
                      >
                        تحرير
                      </Link>
                      <button
                        type="button"
                        onClick={() => setPendingDelete(article)}
                        className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-50"
                      >
                        حذف
                      </button>
                    </>
                  ) : (
                    <Link
                      href={`/maktabi/maqalati/${article.id}`}
                      className="rounded-md border border-[var(--journal-border)] px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
                    >
                      عرض
                    </Link>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <ConfirmDialog
        open={pendingDelete != null}
        title="حذف المسودة"
        description={DELETE_CONFIRM}
        confirmLabel="حذف نهائياً"
        submitting={deleting}
        onConfirm={() => void handleConfirmDelete()}
        onCancel={() => {
          if (!deleting) setPendingDelete(null);
        }}
      />
    </div>
  );
}
