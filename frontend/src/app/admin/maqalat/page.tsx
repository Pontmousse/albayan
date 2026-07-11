"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import {
  listAdminArticles,
  type AdminArticleSummary,
} from "@/lib/api/admin";
import type { VersionStatus } from "@/lib/api/articles";
import { formatDate } from "@/lib/format-date";

type Filter = "all" | VersionStatus;

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "الكل" },
  { id: "draft", label: "مسودات" },
  { id: "submitted", label: "مُقدَّمة" },
  { id: "under_review", label: "قيد المراجعة" },
  { id: "accepted", label: "مقبولة" },
  { id: "rejected", label: "مرفوضة" },
  { id: "published", label: "منشورة" },
];

function matchesFilter(row: AdminArticleSummary, filter: Filter): boolean {
  if (filter === "all") return true;
  return row.status === filter;
}

export default function AdminArticlesPage() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AdminArticleSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    let cancelled = false;
    listAdminArticles(getToken)
      .then((data) => {
        if (!cancelled) setRows(data);
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

  const filtered = rows?.filter((row) => matchesFilter(row, filter)) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          المقالات
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          جميع مقالات المنصة — عيّن مراجعين ومحررين وأدر الدعوات من صفحة التفاصيل.
        </p>
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
                  : "border-amber-200 bg-white/70 text-slate-600 hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
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
      ) : rows === null ? (
        <RowsSkeleton count={6} />
      ) : rows.length === 0 ? (
        <EmptyState
          title="لا مقالات"
          description="لم تُنشأ مقالات بعد في المنصة."
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="لا نتائج لهذا الفلتر"
          description="جرّب فلتراً آخر لعرض المقالات."
        />
      ) : (
        <ul className="space-y-2.5">
          {filtered.map((row, index) => {
            const primaryAuthor =
              row.authors[0]?.user.full_name ||
              row.authors[0]?.user.email ||
              "—";
            return (
              <li
                key={row.id}
                className="stagger-item"
                style={{ "--stagger-index": index } as React.CSSProperties}
              >
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md">
                  <div className="min-w-0 flex-1">
                    <Link
                      href={`/admin/maqalat/${row.id}`}
                      className="block truncate text-sm font-semibold text-slate-800 hover:text-[var(--journal-accent-strong)]"
                    >
                      {row.title}
                    </Link>
                    <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span>{primaryAuthor}</span>
                      <span aria-hidden>·</span>
                      <span>v{row.version_number}</span>
                      <span aria-hidden>·</span>
                      <span>{row.reviewers.length} مراجع</span>
                      <span aria-hidden>·</span>
                      <span>{row.editors.length} محرر</span>
                      <span aria-hidden>·</span>
                      <span>{formatDate(row.updated_at)}</span>
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <StatusBadge status={row.status} />
                    <Link
                      href={`/admin/maqalat/${row.id}`}
                      className="rounded-md border border-amber-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
                    >
                      إدارة
                    </Link>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
