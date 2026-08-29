"use client";

import { useAuth } from "@clerk/nextjs";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import {
  createIssue,
  ISSUE_CATEGORY_LABELS,
  ISSUE_STATUS_LABELS,
  listIssues,
  removeIssueUpvote,
  upvoteIssue,
  type IssueCategory,
  type IssueRead,
  type IssueStatus,
} from "@/lib/api/issues";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate, formatRelativeTime } from "@/lib/format-date";

type StatusFilter = "all" | IssueStatus;
type CategoryFilter = "all" | IssueCategory;
type IssueSort = "date" | "upvotes";
type SortDirection = "asc" | "desc";

const CATEGORIES: IssueCategory[] = ["bug", "feature_request", "feedback"];
const STATUSES: IssueStatus[] = ["open", "in_progress", "resolved", "closed"];

const STATUS_CLASS: Record<IssueStatus, string> = {
  open: "border-emerald-200 bg-emerald-50 text-emerald-800",
  in_progress: "border-sky-200 bg-sky-50 text-sky-800",
  resolved: "border-violet-200 bg-violet-50 text-violet-800",
  closed: "border-slate-200 bg-slate-100 text-slate-700",
};

export default function BalaghatPage() {
  const { getToken } = useAuth();
  const [issues, setIssues] = useState<IssueRead[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<IssueCategory>("bug");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [sort, setSort] = useState<IssueSort>("date");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [votingId, setVotingId] = useState<string | null>(null);
  const queryIssueLoadedRef = useRef(false);

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
    return listIssues(getToken, listParams)
      .then((rows) => {
        setIssues(rows);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "تعذّر تحميل البلاغات.");
      });
  }, [getToken, listParams]);

  useEffect(() => {
    let cancelled = false;
    listIssues(getToken, listParams)
      .then((rows) => {
        if (!cancelled) setIssues(rows);
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

  useEffect(() => {
    if (queryIssueLoadedRef.current) return;
    queryIssueLoadedRef.current = true;
    const issueId = new URLSearchParams(window.location.search).get("issue");
    if (issueId) setSelectedId(issueId);
  }, []);

  const selectedIssue = useMemo(
    () => issues?.find((issue) => issue.id === selectedId) ?? null,
    [issues, selectedId],
  );

  function selectIssue(issueId: string) {
    const next = selectedId === issueId ? null : issueId;
    setSelectedId(next);
    const url = new URL(window.location.href);
    if (next) {
      url.searchParams.set("issue", next);
    } else {
      url.searchParams.delete("issue");
    }
    window.history.replaceState(null, "", `${url.pathname}${url.search}`);
  }

  function applyIssueUpdate(updated: IssueRead) {
    setIssues((rows) =>
      rows?.map((issue) => (issue.id === updated.id ? updated : issue)) ?? rows,
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await createIssue(getToken, { title, description, category });
      setTitle("");
      setDescription("");
      setCategory("bug");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر إرسال البلاغ.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVote(issue: IssueRead) {
    if (votingId) return;
    const previous = issues ?? [];
    const optimistic: IssueRead = {
      ...issue,
      current_user_upvoted: !issue.current_user_upvoted,
      upvote_count: issue.current_user_upvoted
        ? Math.max(0, issue.upvote_count - 1)
        : issue.upvote_count + 1,
    };
    setVotingId(issue.id);
    applyIssueUpdate(optimistic);
    setError(null);

    try {
      const updated = issue.current_user_upvoted
        ? await removeIssueUpvote(getToken, issue.id)
        : await upvoteIssue(getToken, issue.id);
      applyIssueUpdate(updated);
    } catch (err) {
      setIssues(previous);
      setError(err instanceof Error ? err.message : "تعذّر تحديث التصويت.");
    } finally {
      setVotingId(null);
    }
  }

  const canSubmit =
    title.trim().length > 0 && description.trim().length > 0 && !submitting;

  return (
    <div className="space-y-6">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          البلاغات
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          بلاغات وملاحظات مستخدمي المنصة.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-[var(--journal-border)] bg-white/85 p-4 shadow-sm"
      >
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem]">
          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-slate-700">
              العنوان
            </span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={500}
              className="h-11 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-slate-700">
              التصنيف
            </span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value as IssueCategory)}
              className="h-11 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
            >
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {ISSUE_CATEGORY_LABELS[item]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold text-slate-700">
            الوصف
          </span>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={20_000}
            rows={4}
            className="min-h-28 w-full resize-y rounded-md border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
          />
        </label>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!canSubmit}
            className={`${buttonClassName} disabled:cursor-not-allowed disabled:opacity-60`}
          >
            {submitting ? "جارٍ الإرسال..." : "إرسال بلاغ"}
          </button>
        </div>
      </form>

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
            {CATEGORIES.map((item) => (
              <option key={item} value={item}>
                {ISSUE_CATEGORY_LABELS[item]}
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
        <RowsSkeleton count={4} />
      ) : issues !== null && issues.length === 0 ? (
        <EmptyState
          title="لا نتائج"
          description="لا توجد بلاغات تطابق الفلاتر الحالية."
        />
      ) : issues !== null ? (
        <ul className="space-y-2.5">
          {issues.map((issue, index) => (
            <li
              key={issue.id}
              className="stagger-item"
              style={{ "--stagger-index": index } as CSSProperties}
            >
              <article
                className={`rounded-lg border bg-white/85 px-4 py-3.5 shadow-sm transition ${
                  selectedId === issue.id
                    ? "border-[var(--journal-accent)] ring-2 ring-[var(--journal-accent-soft)]"
                    : "border-[var(--journal-border)] hover:border-[var(--journal-accent)]"
                }`}
              >
                <button
                  type="button"
                  onClick={() => selectIssue(issue.id)}
                  className="block w-full text-start"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h2 className="text-sm font-semibold text-slate-900">
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
                    <time dateTime={issue.created_at}>
                      {formatRelativeTime(issue.created_at)}
                    </time>
                    <span aria-hidden>·</span>
                    <span>تاريخ الإنشاء: {formatDate(issue.created_at)}</span>
                    <span aria-hidden>·</span>
                    <span>{issue.reporter.full_name ?? "مستخدم البيان"}</span>
                  </div>
                </button>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                  <button
                    type="button"
                    disabled={votingId === issue.id}
                    onClick={() => handleVote(issue)}
                    className={`inline-flex min-h-9 items-center justify-center rounded-md border px-3 text-xs font-semibold transition disabled:cursor-wait disabled:opacity-70 ${
                      issue.current_user_upvoted
                        ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white"
                        : "border-[var(--journal-border)] bg-white text-slate-700 hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
                    }`}
                  >
                    {issue.current_user_upvoted ? "صوّتَّ" : "تصويت"} ·{" "}
                    {issue.upvote_count}
                  </button>
                  <button
                    type="button"
                    onClick={() => selectIssue(issue.id)}
                    className="rounded-md px-2 py-1 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
                  >
                    {selectedId === issue.id ? "إخفاء التفاصيل" : "عرض التفاصيل"}
                  </button>
                </div>

                {selectedId === issue.id ? (
                  <div className="mt-4 border-t border-[var(--journal-border)] pt-4">
                    <div className="rounded-md bg-slate-50 px-3 py-3">
                      <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                        {selectedIssue?.description ?? issue.description}
                      </p>
                    </div>
                    {issue.images.length > 0 ? (
                      <div className="mt-3 grid gap-2 sm:grid-cols-3">
                        {issue.images.map((image) => (
                          <div
                            key={image.id}
                            className="rounded-md border border-[var(--journal-border)] bg-white px-3 py-2 text-xs text-slate-500"
                          >
                            {image.s3_key}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </article>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
