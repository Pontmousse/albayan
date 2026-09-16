"use client";

import { useCallback, useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import { useNumerals } from "@/components/numeral-provider";
import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import {
  getDraftRevision,
  listDraftRevisions,
  type DraftRevisionHistoryDetail,
  type DraftRevisionHistoryItem,
} from "@/lib/api/articles";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;

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

function creatorLabel(revision: DraftRevisionHistoryItem): string {
  if (revision.created_by_name?.trim()) return revision.created_by_name;
  if (revision.actor_type === "agent") return "وكيل المقال";
  if (revision.actor_type === "system") return "النظام";
  return "مؤلف المقال";
}

export function DraftHistoryDialog({
  open,
  articleId,
  getToken,
  onClose,
  onRestore,
}: {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  onClose: () => void;
  onRestore: (revision: DraftRevisionHistoryItem) => Promise<void>;
}) {
  const { formatDateTime, formatDigits } = useNumerals();
  const [revisions, setRevisions] = useState<DraftRevisionHistoryItem[]>([]);
  const [selected, setSelected] = useState<DraftRevisionHistoryItem | null>(null);
  const [detail, setDetail] = useState<DraftRevisionHistoryDetail | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [restoring, setRestoring] = useState(false);

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
      setError(userFacingErrorMessage(err, "تعذّر تحميل سجل المسودة."));
    } finally {
      setLoadingList(false);
    }
  }, [articleId, getToken]);

  useEffect(() => {
    if (!open) return;
    setDetail(null);
    void loadList();
  }, [open, loadList]);

  useEffect(() => {
    if (!open || !selected) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoadingDetail(true);
    setDetail(null);
    setError(null);
    getDraftRevision(getToken, articleId, selected.revision_id)
      .then((value) => {
        if (!cancelled) setDetail(value);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(userFacingErrorMessage(err, "تعذّر تحميل هذه المراجعة."));
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });
    return () => {
      cancelled = true;
    };
  }, [articleId, getToken, open, selected]);

  async function confirmRestore() {
    if (!selected || selected.is_current) return;
    setRestoring(true);
    setError(null);
    try {
      await onRestore(selected);
      setConfirming(false);
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّرت استعادة المراجعة."));
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
        panelClassName="flex max-h-[94dvh] max-w-6xl flex-col overflow-hidden p-0 sm:p-0"
      >
        <header className="flex items-center justify-between gap-4 border-b border-[var(--journal-border)] px-4 py-4 sm:px-6">
          <div>
            <h2
              id="draft-history-title"
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              سجل المسودة
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              آخر مئة مراجعة محفوظة للمقال
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

        {error ? (
          <div className="mx-4 mt-3 flex items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 sm:mx-6" role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => void loadList()} className="shrink-0 font-semibold underline">
              إعادة المحاولة
            </button>
          </div>
        ) : null}

        <div className="grid min-h-0 flex-1 md:grid-cols-[19rem_minmax(0,1fr)]">
          <aside className="max-h-64 overflow-y-auto border-b border-[var(--journal-border)] bg-white/60 p-3 md:max-h-none md:border-b-0 md:border-e">
            {loadingList ? (
              <div className="space-y-2">
                <SkeletonBlock className="h-20" />
                <SkeletonBlock className="h-20" />
                <SkeletonBlock className="h-20" />
              </div>
            ) : revisions.length === 0 ? (
              <p className="p-4 text-center text-sm text-slate-500">لا توجد مراجعات محفوظة.</p>
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
                          المراجعة {formatDigits(String(revision.revision_number))}
                        </strong>
                        {revision.is_current ? (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">الحالية</span>
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
                          مستعادة من المراجعة {formatDigits(String(revision.restored_from_revision_number))}
                        </span>
                      ) : null}
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </aside>

          <section className="min-h-0 overflow-y-auto p-4 sm:p-6">
            {loadingDetail ? (
              <div className="space-y-3">
                <SkeletonBlock className="h-8 w-1/3" />
                <SkeletonBlock className="h-80" />
              </div>
            ) : detail ? (
              <div>
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-slate-900">
                      معاينة المراجعة {formatDigits(String(detail.revision_number))}
                    </h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatDateTime(new Date(detail.created_at))}
                    </p>
                  </div>
                  {!detail.is_current ? (
                    <button
                      type="button"
                      onClick={() => setConfirming(true)}
                      className="min-h-10 rounded-md bg-[var(--journal-accent-strong)] px-4 text-sm font-semibold text-white transition hover:opacity-90"
                    >
                      استعادة هذه المراجعة
                    </button>
                  ) : null}
                </div>
                <DocumentFrozenPreview
                  documentJson={detail.document}
                  articleId={articleId}
                  getToken={getToken}
                />
              </div>
            ) : !loadingList ? (
              <p className="py-12 text-center text-sm text-slate-500">اختر مراجعة لمعاينتها.</p>
            ) : null}
          </section>
        </div>
      </AnimatedOverlay>

      <ConfirmDialog
        open={confirming}
        title="استعادة مراجعة سابقة"
        description={`ستصبح المراجعة ${selected ? formatDigits(String(selected.revision_number)) : ""} مراجعة جديدة للمسودة. لن تُحذف المراجعات الأحدث، ولن تتغير قائمة مؤلفي المقال.`}
        confirmLabel="استعادة كمراجعة جديدة"
        submitting={restoring}
        onConfirm={() => void confirmRestore()}
        onCancel={() => setConfirming(false)}
      />
    </>
  );
}
