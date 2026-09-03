"use client";

import { useAuth } from "@clerk/nextjs";
import Image from "next/image";
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
import { IssueImageThumbnail } from "@/components/issues/issue-image-thumbnail";
import {
  ResponsiveSelect,
  type ResponsiveSelectOption,
} from "@/components/ui/responsive-select";
import { getCurrentUser } from "@/lib/api";
import {
  createIssueWithImages,
  deleteIssueImage,
  ISSUE_CATEGORY_LABELS,
  ISSUE_STATUS_LABELS,
  listIssues,
  removeIssueUpvote,
  uploadIssueImage,
  upvoteIssue,
  type IssueCategory,
  type IssueRead,
  type IssueStatus,
} from "@/lib/api/issues";
import { buttonClassName } from "@/lib/auth-ui";
import { useNumerals } from "@/components/numeral-provider";

type StatusFilter = "all" | IssueStatus;
type CategoryFilter = "all" | IssueCategory;
type IssueSort = "date" | "upvotes";
type SortDirection = "asc" | "desc";

const CATEGORIES: IssueCategory[] = ["bug", "feature_request", "feedback"];
const STATUSES: IssueStatus[] = ["open", "in_progress", "resolved", "closed"];
const MAX_SELECTED_IMAGES = 3;

const CATEGORY_OPTIONS: ResponsiveSelectOption<IssueCategory>[] = CATEGORIES.map(
  (value) => ({ value, label: ISSUE_CATEGORY_LABELS[value] }),
);
const STATUS_FILTER_OPTIONS: ResponsiveSelectOption<StatusFilter>[] = [
  { value: "all", label: "كل الحالات" },
  ...STATUSES.map((value) => ({ value, label: ISSUE_STATUS_LABELS[value] })),
];
const CATEGORY_FILTER_OPTIONS: ResponsiveSelectOption<CategoryFilter>[] = [
  { value: "all", label: "كل التصنيفات" },
  ...CATEGORY_OPTIONS,
];
const SORT_OPTIONS: ResponsiveSelectOption<IssueSort>[] = [
  { value: "date", label: "التاريخ" },
  { value: "upvotes", label: "التصويتات" },
];
const DIRECTION_OPTIONS: ResponsiveSelectOption<SortDirection>[] = [
  { value: "desc", label: "تنازلي" },
  { value: "asc", label: "تصاعدي" },
];

const STATUS_CLASS: Record<IssueStatus, string> = {
  open: "border-emerald-200 bg-emerald-50 text-emerald-800",
  in_progress: "border-sky-200 bg-sky-50 text-sky-800",
  resolved: "border-violet-200 bg-violet-50 text-violet-800",
  closed: "border-slate-200 bg-slate-100 text-slate-700",
};

export default function BalaghatPage() {
  const { formatDate, formatNumber, formatRelativeTime } = useNumerals();
  const { getToken } = useAuth();
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [issues, setIssues] = useState<IssueRead[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<IssueCategory>("bug");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [filePreviews, setFilePreviews] = useState<
    { url: string; name: string; size: number }[]
  >([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [sort, setSort] = useState<IssueSort>("date");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [votingId, setVotingId] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<string | null>(null);
  const queryIssueLoadedRef = useRef(false);
  const createFileInputRef = useRef<HTMLInputElement>(null);

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

  useEffect(() => {
    let cancelled = false;
    getCurrentUser(getToken)
      .then((user) => {
        if (!cancelled) setCurrentUserId(user.id);
      })
      .catch(() => {
        if (!cancelled) setCurrentUserId(null);
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  useEffect(() => {
    const previews = selectedFiles.map((file) => ({
      url: URL.createObjectURL(file),
      name: file.name,
      size: file.size,
    }));
    setFilePreviews(previews);
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.url));
    };
  }, [selectedFiles]);

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

  function updateSelectedIssueInUrl(issueId: string | null) {
    const url = new URL(window.location.href);
    if (issueId) {
      url.searchParams.set("issue", issueId);
    } else {
      url.searchParams.delete("issue");
    }
    window.history.replaceState(null, "", `${url.pathname}${url.search}`);
  }

  function handleCreateFiles(files: FileList | null) {
    const next = Array.from(files ?? []);
    if (next.length > MAX_SELECTED_IMAGES) {
      setImageError("يمكن إرفاق ثلاث صور كحد أقصى مع البلاغ.");
      setSelectedFiles([]);
      return;
    }
    setImageError(null);
    setSelectedFiles(next);
  }

  function removeSelectedFile(index: number) {
    setSelectedFiles((files) => files.filter((_, itemIndex) => itemIndex !== index));
    setImageError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const created = await createIssueWithImages(
        getToken,
        { title, description, category },
        selectedFiles,
      );
      setTitle("");
      setDescription("");
      setCategory("bug");
      setSelectedFiles([]);
      if (createFileInputRef.current) createFileInputRef.current.value = "";
      setSelectedId(created.id);
      updateSelectedIssueInUrl(created.id);
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

  async function handleDetailImageUpload(issue: IssueRead, files: FileList | null) {
    const selected = Array.from(files ?? []);
    if (!selected.length || uploadingImage) return;
    if (issue.images.length + selected.length > MAX_SELECTED_IMAGES) {
      setImageError("يمكن إرفاق ثلاث صور كحد أقصى لكل بلاغ.");
      return;
    }

    setUploadingImage(true);
    setImageError(null);
    setError(null);
    try {
      let updated = issue;
      for (const file of selected) {
        updated = await uploadIssueImage(getToken, issue.id, file);
      }
      applyIssueUpdate(updated);
    } catch (err) {
      setImageError(err instanceof Error ? err.message : "تعذّر رفع الصورة.");
    } finally {
      setUploadingImage(false);
    }
  }

  async function handleDeleteImage(issue: IssueRead, imageId: string) {
    if (deletingImageId) return;
    setDeletingImageId(imageId);
    setImageError(null);
    setError(null);
    try {
      const updated = await deleteIssueImage(getToken, issue.id, imageId);
      applyIssueUpdate(updated);
    } catch (err) {
      setImageError(err instanceof Error ? err.message : "تعذّر حذف الصورة.");
    } finally {
      setDeletingImageId(null);
    }
  }

  const canSubmit =
    title.trim().length > 0 && description.trim().length > 0 && !submitting;

  return (
    <main className="mx-auto w-full max-w-6xl space-y-6 px-3 py-5 sm:px-6 sm:py-8 lg:py-12">
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

          <ResponsiveSelect
            label="التصنيف"
            value={category}
            options={CATEGORY_OPTIONS}
            onChange={setCategory}
          />
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

        <div className="space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-slate-700">
              الصور
            </span>
            <input
              ref={createFileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              multiple
              onChange={(event) => handleCreateFiles(event.currentTarget.files)}
              className="block w-full rounded-md border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-700 file:me-3 file:rounded-md file:border-0 file:bg-[var(--journal-accent-soft)] file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-[var(--journal-accent)]"
            />
          </label>

          {imageError ? (
            <p className="text-sm text-red-700" role="alert">
              {imageError}
            </p>
          ) : null}

          {filePreviews.length > 0 ? (
            <div className="grid gap-2 sm:grid-cols-3">
              {filePreviews.map((preview, index) => (
                <div
                  key={`${preview.name}-${preview.size}-${index}`}
                  className="overflow-hidden rounded-md border border-[var(--journal-border)] bg-white"
                >
                  <div className="relative aspect-[4/3]">
                    <Image
                      src={preview.url}
                      alt=""
                      fill
                      unoptimized
                      sizes="(max-width: 640px) 50vw, 220px"
                      className="object-cover"
                    />
                  </div>
                  <div className="flex items-center justify-between gap-2 px-2 py-1.5">
                    <span className="min-w-0 truncate text-xs text-slate-600">
                      {preview.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeSelectedFile(index)}
                      className="shrink-0 rounded-md px-2 py-1 text-xs font-semibold text-red-700 transition hover:bg-red-50"
                    >
                      حذف
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

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
        <ResponsiveSelect
          label="الحالة"
          value={statusFilter}
          options={STATUS_FILTER_OPTIONS}
          onChange={setStatusFilter}
        />
        <ResponsiveSelect
          label="التصنيف"
          value={categoryFilter}
          options={CATEGORY_FILTER_OPTIONS}
          onChange={setCategoryFilter}
        />
        <ResponsiveSelect
          label="الترتيب"
          value={sort}
          options={SORT_OPTIONS}
          onChange={setSort}
        />
        <ResponsiveSelect
          label="الاتجاه"
          value={direction}
          options={DIRECTION_OPTIONS}
          onChange={setDirection}
        />
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
                    {formatNumber(issue.upvote_count)}
                  </button>
                  <button
                    type="button"
                    onClick={() => selectIssue(issue.id)}
                    className="rounded-md px-2 py-1 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
                  >
                    {selectedId === issue.id ? "إخفاء التفاصيل" : "عرض التفاصيل"}
                  </button>
                </div>

                {selectedId === issue.id
                  ? (() => {
                      const detailIssue =
                        selectedIssue?.id === issue.id ? selectedIssue : issue;
                      const canManageImages =
                        currentUserId !== null &&
                        currentUserId === detailIssue.user_id;
                      const remainingSlots =
                        MAX_SELECTED_IMAGES - detailIssue.images.length;
                      return (
                        <div className="mt-4 border-t border-[var(--journal-border)] pt-4">
                          <div className="rounded-md bg-slate-50 px-3 py-3">
                            <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                              {detailIssue.description}
                            </p>
                          </div>

                          <div className="mt-3 space-y-3">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <h3 className="text-xs font-semibold text-slate-700">
                                الصور
                              </h3>
                              {canManageImages && remainingSlots > 0 ? (
                                <label className="inline-flex min-h-9 cursor-pointer items-center rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]">
                                  {uploadingImage ? "جارٍ الرفع..." : "إضافة صور"}
                                  <input
                                    type="file"
                                    accept="image/jpeg,image/png,image/gif,image/webp"
                                    multiple
                                    disabled={uploadingImage}
                                    onChange={(event) => {
                                      void handleDetailImageUpload(
                                        detailIssue,
                                        event.currentTarget.files,
                                      );
                                      event.currentTarget.value = "";
                                    }}
                                    className="sr-only"
                                  />
                                </label>
                              ) : null}
                            </div>

                            {imageError ? (
                              <p className="text-sm text-red-700" role="alert">
                                {imageError}
                              </p>
                            ) : null}

                            {detailIssue.images.length > 0 ? (
                              <div className="grid gap-2 sm:grid-cols-3">
                                {detailIssue.images.map((image) => (
                                  <IssueImageThumbnail
                                    key={image.id}
                                    issueId={detailIssue.id}
                                    image={image}
                                    deleting={deletingImageId === image.id}
                                    onDelete={
                                      canManageImages
                                        ? (imageId) =>
                                            void handleDeleteImage(
                                              detailIssue,
                                              imageId,
                                            )
                                        : undefined
                                    }
                                  />
                                ))}
                              </div>
                            ) : (
                              <p className="rounded-md border border-dashed border-[var(--journal-border)] bg-white px-3 py-4 text-center text-xs text-slate-500">
                                لا توجد صور مرفقة.
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })()
                  : null}
              </article>
            </li>
          ))}
        </ul>
      ) : null}
    </main>
  );
}
