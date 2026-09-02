"use client";

import { useAuth } from "@clerk/nextjs";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
} from "react";
import { IssueImageThumbnail } from "@/components/issues/issue-image-thumbnail";
import {
  type AdminIssueRead,
  listAdminIssues,
  updateIssueStatus,
} from "@/lib/api/admin";
import {
  ISSUE_CATEGORY_LABELS,
  ISSUE_STATUS_LABELS,
  type IssueCategory,
  type IssueStatus,
} from "@/lib/api/issues";
import { useNumerals } from "@/components/numeral-provider";

type StatusFilter = "all" | IssueStatus;
type CategoryFilter = "all" | IssueCategory;
type IssueSort = "date" | "upvotes";
type SortDirection = "asc" | "desc";

const STATUSES: IssueStatus[] = ["open", "in_progress", "resolved", "closed"];
const CATEGORIES: IssueCategory[] = ["bug", "feature_request", "feedback"];

const STATUS_CLASS: Record<IssueStatus, string> = {
  open: "border-emerald-200 bg-emerald-50 text-emerald-800",
  in_progress: "border-sky-200 bg-sky-50 text-sky-800",
  resolved: "border-violet-200 bg-violet-50 text-violet-800",
  closed: "border-slate-200 bg-slate-100 text-slate-700",
};

export default function AdminBalaghatPage() {
  const { formatDate, formatNumber, formatRelativeTime } = useNumerals();
  const { getToken } = useAuth();
  const [issues, setIssues] = useState<AdminIssueRead[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [sort, setSort] = useState<IssueSort>("date");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const listParams = useMemo(
    () => ({
      status: statusFilter === "all" ? null : statusFilter,
      category: categoryFilter === "all" ? null : categoryFilter,
      sort,
      direction,
    }),
    [categoryFilter, direction, sort, statusFilter],
  );

  const load = useCallback(() => {
    return listAdminIssues(getToken, listParams)
      .then((rows) => {
        setIssues(rows);
        setError(null);
        setSelectedId((current) =>
          current && rows.some((issue) => issue.id === current)
            ? current
            : rows[0]?.id ?? null,
        );
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "تعذّر تحميل البلاغات.");
      });
  }, [getToken, listParams]);

  useEffect(() => {
    let cancelled = false;
    listAdminIssues(getToken, listParams)
      .then((rows) => {
        if (cancelled) return;
        setIssues(rows);
        setError(null);
        setSelectedId((current) =>
          current && rows.some((issue) => issue.id === current)
            ? current
            : rows[0]?.id ?? null,
        );
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل البلاغات.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken, listParams]);

  const selectedIssue = useMemo(
    () => issues?.find((issue) => issue.id === selectedId) ?? null,
    [issues, selectedId],
  );

  function applyIssueUpdate(updated: AdminIssueRead) {
    setIssues((rows) =>
      rows?.map((issue) => (issue.id === updated.id ? updated : issue)) ?? rows,
    );
  }

  async function handleStatusChange(issue: AdminIssueRead, status: IssueStatus) {
    if (issue.status === status) return;
    const previous = issues ?? [];
    const optimistic = { ...issue, status };
    setUpdatingId(issue.id);
    setError(null);
    applyIssueUpdate(optimistic);
    try {
      const updated = await updateIssueStatus(getToken, issue.id, status);
      applyIssueUpdate(updated);
    } catch (err) {
      setIssues(previous);
      setError(err instanceof Error ? err.message : "تعذّر تحديث حالة البلاغ.");
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            إدارة البلاغات
          </h1>
          <p className="mt-1.5 text-sm text-slate-600">
            متابعة بلاغات المستخدمين وتحديث حالاتها.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-md border border-[var(--journal-border)] bg-white px-4 py-2 text-sm font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
        >
          تحديث
        </button>
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      <div className="grid gap-3 rounded-lg border border-[var(--journal-border)] bg-white/75 p-3 shadow-sm sm:grid-cols-4">
        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold text-slate-700">
            الحالة
          </span>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            className="h-10 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
          >
            <option value="all">كل الحالات</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {ISSUE_STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold text-slate-700">
            التصنيف
          </span>
          <select
            value={categoryFilter}
            onChange={(event) =>
              setCategoryFilter(event.target.value as CategoryFilter)
            }
            className="h-10 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
          >
            <option value="all">كل التصنيفات</option>
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {ISSUE_CATEGORY_LABELS[category]}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold text-slate-700">
            الترتيب
          </span>
          <select
            value={sort}
            onChange={(event) => setSort(event.target.value as IssueSort)}
            className="h-10 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
          >
            <option value="date">التاريخ</option>
            <option value="upvotes">التصويتات</option>
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold text-slate-700">
            الاتجاه
          </span>
          <select
            value={direction}
            onChange={(event) => setDirection(event.target.value as SortDirection)}
            className="h-10 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
          >
            <option value="desc">تنازلي</option>
            <option value="asc">تصاعدي</option>
          </select>
        </label>
      </div>

      {issues === null && !error ? (
        <div className="rounded-lg border border-[var(--journal-border)] bg-white/75 p-4">
          <p className="text-sm text-slate-500">جارٍ تحميل البلاغات...</p>
        </div>
      ) : issues !== null && issues.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[var(--journal-border)] bg-white/60 px-4 py-10 text-center">
          <h2 className="text-base font-bold text-slate-900">لا بلاغات</h2>
          <p className="mt-1.5 text-sm text-slate-600">
            لا توجد بلاغات تطابق الفلاتر الحالية.
          </p>
        </div>
      ) : issues !== null ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,24rem)]">
          <ul className="space-y-2.5">
            {issues.map((issue, index) => (
              <li
                key={issue.id}
                className="stagger-item"
                style={{ "--stagger-index": index } as CSSProperties}
              >
                <button
                  type="button"
                  onClick={() => setSelectedId(issue.id)}
                  className={`block w-full rounded-lg border bg-white/85 px-4 py-3.5 text-start shadow-sm transition ${
                    selectedId === issue.id
                      ? "border-[var(--journal-accent)] ring-2 ring-[var(--journal-accent-soft)]"
                      : "border-[var(--journal-border)] hover:border-[var(--journal-accent)]"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h2 className="truncate text-sm font-semibold text-slate-900">
                        {issue.title}
                      </h2>
                      <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">
                        {issue.description}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold ${STATUS_CLASS[issue.status]}`}
                    >
                      {ISSUE_STATUS_LABELS[issue.status]}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{ISSUE_CATEGORY_LABELS[issue.category]}</span>
                    <span aria-hidden>·</span>
                    <span>{formatNumber(issue.upvote_count)} تصويت</span>
                    <span aria-hidden>·</span>
                    <time dateTime={issue.created_at}>
                      {formatRelativeTime(issue.created_at)}
                    </time>
                  </div>
                </button>
              </li>
            ))}
          </ul>

          <aside className="rounded-lg border border-[var(--journal-border)] bg-white/85 p-4 shadow-sm lg:sticky lg:top-28 lg:self-start">
            {selectedIssue ? (
              <div className="space-y-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    {selectedIssue.title}
                  </h2>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                    {selectedIssue.description}
                  </p>
                </div>

                <label className="block">
                  <span className="mb-1.5 block text-xs font-semibold text-slate-700">
                    تحديث الحالة
                  </span>
                  <select
                    value={selectedIssue.status}
                    disabled={updatingId === selectedIssue.id}
                    onChange={(event) =>
                      handleStatusChange(
                        selectedIssue,
                        event.target.value as IssueStatus,
                      )
                    }
                    className="h-10 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)] disabled:cursor-wait disabled:opacity-70"
                  >
                    {STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {ISSUE_STATUS_LABELS[status]}
                      </option>
                    ))}
                  </select>
                </label>

                <dl className="grid gap-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">المراسل</dt>
                    <dd className="min-w-0 truncate font-medium text-slate-800">
                      {selectedIssue.reporter.full_name ?? "مستخدم البيان"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">البريد</dt>
                    <dd className="min-w-0 truncate font-medium text-slate-800">
                      {selectedIssue.reporter.email}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">التصويتات</dt>
                    <dd className="font-medium text-slate-800">
                      {formatNumber(selectedIssue.upvote_count)}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">أُنشئ</dt>
                    <dd className="font-medium text-slate-800">
                      {formatDate(selectedIssue.created_at)}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">آخر تحديث</dt>
                    <dd className="font-medium text-slate-800">
                      {formatDate(selectedIssue.updated_at)}
                    </dd>
                  </div>
                </dl>

                {selectedIssue.images.length > 0 ? (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-slate-700">
                      الصور
                    </h3>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {selectedIssue.images.map((image) => (
                        <IssueImageThumbnail
                          key={image.id}
                          issueId={selectedIssue.id}
                          image={image}
                        />
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-slate-500">اختر بلاغاً لعرض تفاصيله.</p>
            )}
          </aside>
        </div>
      ) : null}
    </div>
  );
}
