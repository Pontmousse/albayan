"use client";

import type { Document2Json } from "@drghaliasri/butex/document2";
import {
  ArrowLeftRight,
  Eye,
  EyeOff,
  FileText,
  Minus,
  Pencil,
  Plus,
  Sparkles,
  Tag,
  type LucideIcon,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import { useNumerals } from "@/components/numeral-provider";
import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import {
  getDraftRevision,
  listDraftRevisions,
  type DraftRevisionHistoryItem,
} from "@/lib/api/articles";
import {
  getDraftRevisionChangeSummary,
  type RevisionChangeKind,
  type RevisionChangeSummaryV1,
} from "@/lib/api/revision-change-summary";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;

type ChangeKindVisual = {
  label: string;
  icon: LucideIcon;
  className: string;
  iconClassName: string;
};

const ACTOR_LABELS: Record<DraftRevisionHistoryItem["actor_type"], string> = {
  human: "تعديل بشري",
  agent: "تعديل وكيل",
  system: "تعديل النظام",
};

const REASON_LABELS: Record<DraftRevisionHistoryItem["reason"], string> = {
  initial: "المسودة الأولى",
  autosave: "حفظ تلقائي",
  ai_edit: "تعديل بالوكيل",
  metadata_edit: "تعديل العنوان أو الملخص",
  restore: "استعادة",
  revision_request: "فتح جولة تعديل",
};

export const CHANGE_KIND_VISUALS: Record<RevisionChangeKind, ChangeKindVisual> = {
  added: {
    label: "إضافة",
    icon: Plus,
    className: "border-emerald-200 bg-emerald-50/70",
    iconClassName: "bg-emerald-100 text-emerald-700",
  },
  removed: {
    label: "حذف",
    icon: Minus,
    className: "border-rose-200 bg-rose-50/70",
    iconClassName: "bg-rose-100 text-rose-700",
  },
  edited: {
    label: "تعديل",
    icon: Pencil,
    className: "border-amber-200 bg-amber-50/70",
    iconClassName: "bg-amber-100 text-amber-800",
  },
  moved: {
    label: "نقل",
    icon: ArrowLeftRight,
    className: "border-sky-200 bg-sky-50/70",
    iconClassName: "bg-sky-100 text-sky-700",
  },
  metadata: {
    label: "بيانات المستند",
    icon: Tag,
    className: "border-violet-200 bg-violet-50/70",
    iconClassName: "bg-violet-100 text-violet-700",
  },
  other: {
    label: "تغيير",
    icon: FileText,
    className: "border-slate-200 bg-slate-50/80",
    iconClassName: "bg-slate-200 text-slate-700",
  },
};

export function changeKindVisual(kind: string): ChangeKindVisual {
  return CHANGE_KIND_VISUALS[kind as RevisionChangeKind] ?? CHANGE_KIND_VISUALS.other;
}

function creatorLabel(revision: DraftRevisionHistoryItem): string {
  if (revision.created_by_name?.trim()) return revision.created_by_name;
  if (revision.actor_type === "agent") return "وكيل المقال";
  if (revision.actor_type === "system") return "النظام";
  return "مؤلف المقال";
}

function ChangeSummary({
  summary,
  loading,
  unavailable,
}: {
  summary: RevisionChangeSummaryV1 | null;
  loading: boolean;
  unavailable: boolean;
}) {
  return (
    <div className="rounded-xl border border-[var(--journal-border)] bg-white/70 p-4 sm:p-5">
      <div className="mb-4 flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-full bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
          <Sparkles className="size-4" aria-hidden="true" />
        </span>
        <div>
          <h4 className="font-bold text-slate-900">التغييرات في هذه النسخة</h4>
          <p className="mt-0.5 text-xs text-slate-500">
            وصف مختصر لما تغيّر مقارنةً بالنسخة السابقة
          </p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-2" aria-label="جارٍ تحميل وصف التغييرات">
          <SkeletonBlock className="h-14" />
          <SkeletonBlock className="h-14" />
          <SkeletonBlock className="h-14 w-5/6" />
        </div>
      ) : unavailable || summary === null ? (
        <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50/70 px-4 py-5 text-center text-sm leading-7 text-slate-500">
          لا يتوفر وصف مختصر للتغييرات في هذه النسخة.
        </p>
      ) : summary.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50/70 px-4 py-5 text-center text-sm leading-7 text-slate-500">
          لم تُسجّل تغييرات ذات معنى بين هذه النسخة والتي قبلها.
        </p>
      ) : (
        <ul className="space-y-2.5">
          {summary.items.map((item, index) => {
            const visual = changeKindVisual(item.kind);
            const Icon = visual.icon;
            return (
              <li
                key={`${item.kind}-${index}`}
                className={`flex gap-3 rounded-lg border px-3.5 py-3 ${visual.className}`}
              >
                <span
                  className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ${visual.iconClassName}`}
                  title={visual.label}
                  aria-label={visual.label}
                >
                  <Icon className="size-3.5" aria-hidden="true" />
                </span>
                <p className="text-sm leading-7 text-slate-800">{item.text}</p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function DraftHistoryDialog({
  open,
  articleId,
  getToken,
  onClose,
  onRestore,
  latestChangesUnsaved = false,
  currentDocument = null,
}: {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  onClose: () => void;
  onRestore: (revision: DraftRevisionHistoryItem) => Promise<void>;
  latestChangesUnsaved?: boolean;
  /** Optional #101 fast path for the already-loaded persisted current revision. */
  currentDocument?: Document2Json | null;
}) {
  const { formatDateTime, formatDigits } = useNumerals();
  const [revisions, setRevisions] = useState<DraftRevisionHistoryItem[]>([]);
  const [selected, setSelected] = useState<DraftRevisionHistoryItem | null>(null);
  const [summary, setSummary] = useState<RevisionChangeSummaryV1 | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryUnavailable, setSummaryUnavailable] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDocument, setPreviewDocument] = useState<Document2Json | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const previewRequestRef = useRef(0);

  const loadList = useCallback(async () => {
    setLoadingList(true);
    setError(null);
    try {
      const rows = await listDraftRevisions(getToken, articleId);
      setRevisions(rows);
      setSelected((current) => {
        if (current) {
          const refreshed = rows.find((row) => row.revision_id === current.revision_id);
          if (refreshed) return refreshed;
        }
        return rows.find((row) => row.is_current) ?? rows[0] ?? null;
      });
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل سجل النسخ."));
    } finally {
      setLoadingList(false);
    }
  }, [articleId, getToken]);

  useEffect(() => {
    if (!open) return;
    setPreviewOpen(false);
    setPreviewDocument(null);
    setPreviewError(null);
    setSummary(null);
    setSummaryUnavailable(false);
    void loadList();
  }, [open, loadList]);

  useEffect(() => {
    previewRequestRef.current += 1;
    setPreviewOpen(false);
    setPreviewDocument(null);
    setPreviewError(null);

    if (!open || !selected) {
      setSummary(null);
      setSummaryUnavailable(false);
      setLoadingSummary(false);
      return;
    }

    let cancelled = false;
    setLoadingSummary(true);
    setSummary(null);
    setSummaryUnavailable(false);

    getDraftRevisionChangeSummary(getToken, articleId, selected.revision_id)
      .then(({ summary: value }) => {
        if (!cancelled) {
          setSummary(value);
          setSummaryUnavailable(value === null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSummary(null);
          setSummaryUnavailable(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingSummary(false);
      });

    return () => {
      cancelled = true;
    };
  }, [articleId, getToken, open, selected]);

  async function togglePreview() {
    if (!selected) return;
    if (previewOpen) {
      previewRequestRef.current += 1;
      setPreviewOpen(false);
      setPreviewDocument(null);
      setPreviewError(null);
      setLoadingPreview(false);
      return;
    }

    const requestId = previewRequestRef.current + 1;
    previewRequestRef.current = requestId;
    setPreviewError(null);

    if (selected.is_current && currentDocument && !latestChangesUnsaved) {
      setPreviewDocument(currentDocument);
      setPreviewOpen(true);
      return;
    }

    setLoadingPreview(true);
    try {
      const detail = await getDraftRevision(getToken, articleId, selected.revision_id);
      if (previewRequestRef.current !== requestId) return;
      setPreviewDocument(detail.document);
      setPreviewOpen(true);
    } catch (err) {
      if (previewRequestRef.current !== requestId) return;
      setPreviewError(userFacingErrorMessage(err, "تعذّر تحميل هذه النسخة."));
    } finally {
      if (previewRequestRef.current === requestId) setLoadingPreview(false);
    }
  }

  async function confirmRestore() {
    if (!selected || selected.is_current) return;
    setRestoring(true);
    setError(null);
    try {
      await onRestore(selected);
      setConfirming(false);
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّرت استعادة النسخة."));
      setConfirming(false);
    } finally {
      setRestoring(false);
    }
  }

  return (
    <>
      <AnimatedOverlay
        open={open}
        onClose={onClose}
        labelledBy="draft-history-title"
        panelClassName="flex max-h-[94dvh] flex-col overflow-hidden p-0 sm:h-[94dvh] sm:w-[96vw] sm:max-w-[96rem] sm:p-0"
      >
        <header className="flex items-center justify-between gap-4 border-b border-[var(--journal-border)] px-4 py-4 sm:px-6">
          <div>
            <h2
              id="draft-history-title"
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              سجل النسخ
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              اعرف ما تغيّر أولاً، وافتح المعاينة الكاملة عند الحاجة
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="min-h-10 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-semibold text-slate-600"
          >
            إغلاق
          </button>
        </header>

        <div className="mx-4 mt-3 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs leading-6 text-sky-900 sm:mx-6">
          التراجع والإعادة يخصان جلسة التحرير الحالية فقط. سجل النسخ يحفظ حالات مستقلة على الخادم، ويمكن استعادة أي نسخة محفوظة من دون حذف النسخ الأحدث.
        </div>

        {latestChangesUnsaved ? (
          <div
            className="mx-4 mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-6 text-amber-900 sm:mx-6"
            role="status"
          >
            أحدث تغييرات جلسة التحرير لم تُحفظ بعد. يمكنك قراءة سجل النسخ الآن، لكن الاستعادة لن تبدأ حتى ينجح حفظ هذه التغييرات.
          </div>
        ) : null}

        {error ? (
          <div
            className="mx-4 mt-3 flex items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 sm:mx-6"
            role="alert"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => void loadList()}
              className="shrink-0 font-semibold underline"
            >
              إعادة المحاولة
            </button>
          </div>
        ) : null}

        <div className="grid min-h-0 flex-1 md:grid-cols-[17rem_minmax(0,1fr)] xl:grid-cols-[18rem_minmax(0,1fr)]">
          <aside className="max-h-64 overflow-y-auto border-b border-[var(--journal-border)] bg-white/60 p-3 md:max-h-none md:border-b-0 md:border-e">
            {loadingList ? (
              <div className="space-y-2">
                <SkeletonBlock className="h-20" />
                <SkeletonBlock className="h-20" />
                <SkeletonBlock className="h-20" />
              </div>
            ) : revisions.length === 0 ? (
              <p className="p-4 text-center text-sm text-slate-500">لا توجد نسخ محفوظة.</p>
            ) : (
              <ol className="space-y-2">
                {revisions.map((revision) => (
                  <li key={revision.revision_id}>
                    <button
                      type="button"
                      onClick={() => setSelected(revision)}
                      className={`w-full rounded-lg border p-3 text-start transition ${
                        selected?.revision_id === revision.revision_id
                          ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)]"
                          : "border-[var(--journal-border)] bg-white hover:border-[var(--journal-accent)]"
                      }`}
                    >
                      <span className="flex items-center justify-between gap-2">
                        <strong className="text-sm text-slate-900">
                          النسخة {formatDigits(String(revision.revision_number))}
                        </strong>
                        {revision.is_current ? (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                            الحالية
                          </span>
                        ) : null}
                      </span>
                      <span className="mt-1 block text-xs text-slate-600">
                        {REASON_LABELS[revision.reason]} · {ACTOR_LABELS[revision.actor_type]}
                      </span>
                      <span className="mt-1 block text-xs text-slate-500">
                        {creatorLabel(revision)} · {formatDateTime(new Date(revision.created_at))}
                      </span>
                      {revision.restored_from_revision_number ? (
                        <span className="mt-1 block text-xs font-medium text-amber-800">
                          مستعادة من النسخة {formatDigits(String(revision.restored_from_revision_number))}
                        </span>
                      ) : null}
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </aside>

          <section className="min-h-0 overflow-y-auto p-4 sm:p-6 lg:p-8">
            {selected ? (
              <div className="mx-auto w-full max-w-5xl">
                <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">
                      النسخة {formatDigits(String(selected.revision_number))}
                    </h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatDateTime(new Date(selected.created_at))} · {REASON_LABELS[selected.reason]}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {!selected.is_current ? (
                      <button
                        type="button"
                        onClick={() => setConfirming(true)}
                        className="min-h-10 rounded-md bg-[var(--journal-accent-strong)] px-4 text-sm font-semibold text-white transition hover:opacity-90"
                      >
                        استعادة هذه النسخة
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => void togglePreview()}
                      disabled={loadingPreview}
                      className="inline-flex min-h-10 items-center gap-2 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] disabled:cursor-wait disabled:opacity-60"
                    >
                      {previewOpen ? (
                        <EyeOff className="size-4" aria-hidden="true" />
                      ) : (
                        <Eye className="size-4" aria-hidden="true" />
                      )}
                      {loadingPreview
                        ? "جارٍ تحميل المعاينة…"
                        : previewOpen
                          ? "إخفاء المعاينة"
                          : "عرض المراجعة كاملة"}
                    </button>
                  </div>
                </div>

                <ChangeSummary
                  summary={summary}
                  loading={loadingSummary}
                  unavailable={summaryUnavailable}
                />

                {previewError ? (
                  <p
                    className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                    role="alert"
                  >
                    {previewError}
                  </p>
                ) : null}

                {loadingPreview ? (
                  <div className="mt-5 space-y-3" aria-label="جارٍ تحميل المعاينة">
                    <SkeletonBlock className="h-8 w-1/3" />
                    <SkeletonBlock className="h-80" />
                  </div>
                ) : null}

                {previewOpen && previewDocument ? (
                  <div className="mt-5">
                    <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                      <Eye className="size-4" aria-hidden="true" />
                      المعاينة الكاملة للنسخة
                    </div>
                    <DocumentFrozenPreview
                      documentJson={previewDocument}
                      articleId={articleId}
                      getToken={getToken}
                    />
                  </div>
                ) : null}
              </div>
            ) : !loadingList ? (
              <p className="py-12 text-center text-sm text-slate-500">
                اختر نسخة لعرض التغييرات فيها.
              </p>
            ) : null}
          </section>
        </div>
      </AnimatedOverlay>

      <ConfirmDialog
        open={confirming}
        title="استعادة نسخة محفوظة"
        description={`ستُستعاد النسخة ${selected ? formatDigits(String(selected.revision_number)) : ""} كنسخة حالية جديدة من المسودة، من دون حذف النسخ الأحدث. بعد الاستعادة يبدأ سجل التراجع والإعادة المحلي من الحالة المستعادة من جديد، وتبقى الحالة التي كانت حالية قبل الاستعادة قابلة للرجوع من سجل النسخ ما دامت ضمن النسخ المحفوظة. لن تتغير قائمة مؤلفي المقال.`}
        confirmLabel="استعادة كنسخة حالية جديدة"
        submitting={restoring}
        onConfirm={() => void confirmRestore()}
        onCancel={() => setConfirming(false)}
      />
    </>
  );
}
