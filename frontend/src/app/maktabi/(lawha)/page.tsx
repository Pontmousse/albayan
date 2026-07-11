"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { listMyArticles, type ArticleSummary } from "@/lib/api/articles";
import {
  listEditorArticles,
  type EditorArticleSummary,
} from "@/lib/api/editor";
import {
  listMyAssignments,
  type AssignmentSummary,
} from "@/lib/api/reviews";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

const ACTIVE_STATUSES = ["submitted", "under_review"] as const;
const DONE_STATUSES = ["accepted", "published"] as const;
const PENDING_EDITOR = ["submitted", "under_review"] as const;

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

function isPendingReview(row: AssignmentSummary): boolean {
  return (
    row.assignment_status !== "completed" && row.review?.status !== "submitted"
  );
}

export default function MaktabiOverviewPage() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [articles, setArticles] = useState<ArticleSummary[] | null>(null);
  const [editorArticles, setEditorArticles] = useState<
    EditorArticleSummary[] | null
  >(null);
  const [assignments, setAssignments] = useState<AssignmentSummary[] | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listMyArticles(getToken).catch(() => [] as ArticleSummary[]),
      listEditorArticles(getToken).catch(() => [] as EditorArticleSummary[]),
      listMyAssignments(getToken).catch(() => [] as AssignmentSummary[]),
    ])
      .then(([authorRows, editorRows, reviewRows]) => {
        if (cancelled) return;
        setArticles(authorRows);
        setEditorArticles(editorRows);
        setAssignments(reviewRows);
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

  const displayName = user?.fullName || user?.firstName || "";
  const drafts = articles?.filter((a) => a.status === "draft").length ?? 0;
  const active =
    articles?.filter((a) =>
      (ACTIVE_STATUSES as readonly string[]).includes(a.status),
    ).length ?? 0;
  const done =
    articles?.filter((a) =>
      (DONE_STATUSES as readonly string[]).includes(a.status),
    ).length ?? 0;
  const recent = articles?.slice(0, 5) ?? [];

  const pendingEditor =
    editorArticles?.filter((a) =>
      (PENDING_EDITOR as readonly string[]).includes(a.status),
    ) ?? [];
  const pendingReviews = assignments?.filter(isPendingReview) ?? [];
  const recentEditor = pendingEditor.slice(0, 3);
  const recentReviews = pendingReviews.slice(0, 3);

  const loading =
    articles === null || editorArticles === null || assignments === null;
  const hasAuthor = (articles?.length ?? 0) > 0;
  const hasEditor = (editorArticles?.length ?? 0) > 0;
  const hasReviewer = (assignments?.length ?? 0) > 0;
  const emptyAll = !loading && !hasAuthor && !hasEditor && !hasReviewer;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {displayName ? `مرحباً، ${displayName}` : "مرحباً بك"}
          </h1>
          <p className="mt-1.5 text-sm text-slate-600">
            لوحة عملك في مجلة البيان — تابع مقالاتك وتعييناتك.
          </p>
        </div>
        <Link href="/maktabi/maqalati/jadid" className={buttonClassName}>
          مقال جديد
        </Link>
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : loading ? (
        <>
          <CardsSkeleton />
          <RowsSkeleton />
        </>
      ) : emptyAll ? (
        <EmptyState
          title="لا مقالات بعد"
          description="ابدأ رحلتك في النشر العلمي — أنشئ مقالك الأول وحرّره عبر محرر البيان."
          actionLabel="ابدأ مقالك الأول"
          actionHref="/maktabi/maqalati/jadid"
        />
      ) : (
        <>
          {hasAuthor ? (
            <div className="grid gap-4 sm:grid-cols-3">
              <SummaryCard label="مسودات" value={drafts} index={0} />
              <SummaryCard label="قيد المراجعة" value={active} index={1} />
              <SummaryCard label="مقبولة ومنشورة" value={done} index={2} />
            </div>
          ) : null}

          {(hasEditor || hasReviewer) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {hasEditor ? (
                <SummaryCard
                  label="بانتظار قرار تحريري"
                  value={pendingEditor.length}
                  index={3}
                />
              ) : null}
              {hasReviewer ? (
                <SummaryCard
                  label="مراجعات معلّقة"
                  value={pendingReviews.length}
                  index={4}
                />
              ) : null}
            </div>
          )}

          {hasEditor && recentEditor.length > 0 ? (
            <section>
              <div className="flex items-center justify-between">
                <h2
                  className="text-lg font-bold text-[var(--journal-accent)]"
                  style={{ fontFamily: "var(--font-display-ar), serif" }}
                >
                  قائمة التحرير
                </h2>
                <Link
                  href="/maktabi/tahriri"
                  className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
                >
                  عرض الكل
                </Link>
              </div>
              <ul className="mt-3 space-y-2.5">
                {recentEditor.map((row, index) => (
                  <li
                    key={row.id}
                    className="stagger-item"
                    style={
                      { "--stagger-index": index + 5 } as React.CSSProperties
                    }
                  >
                    <Link
                      href={`/maktabi/tahriri/${row.id}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md"
                    >
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-800">
                        {row.title}
                      </span>
                      <span className="flex shrink-0 items-center gap-3">
                        <StatusBadge status={row.status} />
                        <span className="text-xs text-slate-500">
                          {formatDate(row.updated_at)}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {hasReviewer && recentReviews.length > 0 ? (
            <section>
              <div className="flex items-center justify-between">
                <h2
                  className="text-lg font-bold text-[var(--journal-accent)]"
                  style={{ fontFamily: "var(--font-display-ar), serif" }}
                >
                  مراجعات معلّقة
                </h2>
                <Link
                  href="/maktabi/murajaati"
                  className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
                >
                  عرض الكل
                </Link>
              </div>
              <ul className="mt-3 space-y-2.5">
                {recentReviews.map((row, index) => (
                  <li
                    key={row.id}
                    className="stagger-item"
                    style={
                      { "--stagger-index": index + 8 } as React.CSSProperties
                    }
                  >
                    <Link
                      href={`/maktabi/murajaati/${row.id}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md"
                    >
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-800">
                        {row.article_title}
                      </span>
                      <span className="flex shrink-0 items-center gap-3">
                        <StatusBadge status={row.version_status} />
                        <span className="text-xs text-slate-500">
                          {formatDate(row.invited_at)}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {hasAuthor ? (
            <section>
              <div className="flex items-center justify-between">
                <h2
                  className="text-lg font-bold text-[var(--journal-accent)]"
                  style={{ fontFamily: "var(--font-display-ar), serif" }}
                >
                  آخر المقالات
                </h2>
                <Link
                  href="/maktabi/maqalati"
                  className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
                >
                  عرض الكل
                </Link>
              </div>
              <ul className="mt-3 space-y-2.5">
                {recent.map((article, index) => (
                  <li
                    key={article.id}
                    className="stagger-item"
                    style={
                      { "--stagger-index": index + 11 } as React.CSSProperties
                    }
                  >
                    <Link
                      href={`/maktabi/maqalati/${article.id}`}
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
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
