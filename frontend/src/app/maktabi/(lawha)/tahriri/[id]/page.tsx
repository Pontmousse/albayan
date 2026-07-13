"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { CompiledPdfViewer } from "@/components/dashboard/compiled-pdf-viewer";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { WorkflowProgress } from "@/components/dashboard/workflow-progress";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";
import {
  fetchEditorAssetBlob,
  fetchEditorPdfBlob,
  getEditorArticle,
  getEditorDocument,
  postEditorDecision,
  type EditorArticleDetail,
  type EditorDecisionStatus,
} from "@/lib/api/editor";
import { RECOMMENDATION_LABELS } from "@/lib/api/reviews";

const DECISIONS: {
  status: EditorDecisionStatus;
  label: string;
  needsConfirm: boolean;
}[] = [
  { status: "under_review", label: "قيد المراجعة", needsConfirm: false },
  { status: "accepted", label: "قبول", needsConfirm: true },
  { status: "rejected", label: "رفض", needsConfirm: true },
];

const DECISION_CONFIRM: Record<
  "accepted" | "rejected",
  { title: string; description: string; confirmLabel: string }
> = {
  accepted: {
    title: "تأكيد قبول المقال",
    description:
      "سيتم تحديث حالة الإصدار الحالي إلى «مقبول». يمكنك إضافة سبب اختياري قبل التأكيد.",
    confirmLabel: "تأكيد القبول",
  },
  rejected: {
    title: "تأكيد رفض المقال",
    description:
      "سيتم تحديث حالة الإصدار الحالي إلى «مرفوض». يمكنك إضافة سبب اختياري قبل التأكيد.",
    confirmLabel: "تأكيد الرفض",
  },
};

export default function TahririDetailPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [article, setArticle] = useState<EditorArticleDetail | null>(null);
  const [documentJson, setDocumentJson] = useState<unknown>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [pendingDecision, setPendingDecision] = useState<
    "accepted" | "rejected" | null
  >(null);
  const [deciding, setDeciding] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionOk, setDecisionOk] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getEditorArticle(getToken, articleId);
      setArticle(data);
      try {
        const doc = await getEditorDocument(getToken, articleId);
        setDocumentJson(doc.document);
      } catch {
        setDocumentJson(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل المقال.");
    }
  }, [getToken, articleId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function applyDecision(status: EditorDecisionStatus) {
    setDeciding(true);
    setDecisionError(null);
    setDecisionOk(null);
    try {
      await postEditorDecision(
        getToken,
        articleId,
        status,
        reason.trim() || null,
      );
      setPendingDecision(null);
      setDecisionOk("تم تحديث القرار التحريري.");
      await load();
    } catch (err) {
      setDecisionError(
        err instanceof Error ? err.message : "تعذّر تحديث القرار.",
      );
    } finally {
      setDeciding(false);
    }
  }

  function handleDecisionClick(
    status: EditorDecisionStatus,
    needsConfirm: boolean,
  ) {
    if (needsConfirm) {
      setPendingDecision(status as "accepted" | "rejected");
      return;
    }
    void applyDecision(status);
  }

  if (error) {
    return (
      <div className="space-y-4">
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
        <button
          type="button"
          onClick={() => router.push("/maktabi/tahriri")}
          className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          العودة إلى تحريري
        </button>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="space-y-6">
        <CardsSkeleton count={1} />
        <RowsSkeleton />
      </div>
    );
  }

  const current = article.current_version;
  const confirmMeta = pendingDecision
    ? DECISION_CONFIRM[pendingDecision]
    : null;

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/maktabi/tahriri"
          className="text-xs font-medium text-slate-500 underline-offset-4 hover:text-[var(--journal-accent)] hover:underline"
        >
          → تحريري
        </Link>
        <div className="mt-2">
          <h1
            className="text-2xl font-bold leading-relaxed text-slate-900 sm:text-3xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {article.title}
          </h1>
          <p className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-slate-500">
            <StatusBadge status={current.status} />
            <span>الإصدار v{current.version_number}</span>
            <span aria-hidden>·</span>
            <span>أُنشئ في {formatDate(article.created_at)}</span>
          </p>
        </div>
      </div>

      {article.abstract ? (
        <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-[var(--journal-accent)]">الملخص</h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">{article.abstract}</p>
        </section>
      ) : null}

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">مسار المخطوطة</h2>
        <div className="mt-3">
          <WorkflowProgress status={current.status} />
        </div>
        <p className="mt-3 text-xs leading-6 text-slate-500">
          المخطوطة للقراءة فقط — القرار التحريري يحدّث الحالة دون تعديل المحتوى.
        </p>
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">الإصدارات</h2>
        <ul className="mt-3 space-y-2">
          {article.versions.map((version) => (
            <li
              key={version.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-3.5 py-2.5 text-sm"
            >
              <span className="flex items-center gap-2.5">
                <span className="font-semibold text-slate-800">
                  v{version.version_number}
                </span>
                <StatusBadge status={version.status} />
              </span>
              <span className="text-xs text-slate-500">
                {version.submitted_at
                  ? `قُدِّم في ${formatDate(version.submitted_at)}`
                  : `أُنشئ في ${formatDate(version.created_at)}`}
              </span>
              {version.change_summary ? (
                <p className="w-full text-xs leading-6 text-slate-500">
                  {version.change_summary}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2
          className="text-lg font-bold text-[var(--journal-accent)]"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          معاينة المخطوطة
        </h2>
        <div className="mt-3">
          <DocumentFrozenPreview
            documentJson={documentJson ?? null}
            articleId={articleId}
            getToken={getToken}
            fetchAssetBlob={fetchEditorAssetBlob}
          />
        </div>
      </section>

      <section>
        <h2
          className="text-lg font-bold text-[var(--journal-accent)]"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          ملفّ المعاينة
        </h2>
        <div className="mt-3">
          <CompiledPdfViewer
            compileStatus={current.compile_status}
            getToken={getToken}
            scopeId={articleId}
            fetchPdfBlob={fetchEditorPdfBlob}
          />
        </div>
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">
          تقارير المراجعين
        </h2>
        {article.reviews.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">
            لا تقارير مُسلَّمة على الإصدار الحالي.
          </p>
        ) : (
          <ul className="mt-3 space-y-3">
            {article.reviews.map((review) => (
              <li
                key={review.id}
                className="rounded-lg border border-[var(--journal-border)] bg-white px-4 py-3 text-sm"
              >
                <p className="font-semibold text-slate-800">
                  {review.reviewer_name || review.reviewer_email}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {review.recommendation
                    ? RECOMMENDATION_LABELS[review.recommendation]
                    : "بدون توصية"}
                  {review.submitted_at
                    ? ` · ${formatDate(review.submitted_at)}`
                    : ""}
                </p>
                {review.comments_to_author ? (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-slate-600">
                      للمؤلف
                    </p>
                    <p className="mt-0.5 whitespace-pre-wrap leading-6 text-slate-700">
                      {review.comments_to_author}
                    </p>
                  </div>
                ) : null}
                {review.comments_to_editor ? (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-slate-600">
                      للمحرر
                    </p>
                    <p className="mt-0.5 whitespace-pre-wrap leading-6 text-slate-700">
                      {review.comments_to_editor}
                    </p>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">
          القرار التحريري
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          حدّث حالة الإصدار الحالي دون تعديل محتوى المخطوطة.
        </p>

        <label className="mt-4 block space-y-1.5">
          <span className="text-xs font-semibold text-slate-600">
            سبب القرار (اختياري)
          </span>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            maxLength={2000}
            className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
            placeholder="يُحفظ مع الإصدار ويظهر في ملخص التغيير."
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2.5">
          {DECISIONS.map((item) => (
            <button
              key={item.status}
              type="button"
              disabled={deciding || current.status === item.status}
              onClick={() =>
                handleDecisionClick(item.status, item.needsConfirm)
              }
              className={
                current.status === item.status
                  ? "rounded-md border border-[var(--journal-accent)] bg-[var(--journal-accent)] px-5 py-2.5 text-sm font-semibold text-white opacity-80"
                  : buttonClassName
              }
            >
              {item.label}
            </button>
          ))}
        </div>

        {decisionError ? (
          <p
            className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {decisionError}
          </p>
        ) : null}
        {decisionOk ? (
          <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {decisionOk}
          </p>
        ) : null}
      </section>

      {confirmMeta && pendingDecision ? (
        <ConfirmDialog
          open
          title={confirmMeta.title}
          description={confirmMeta.description}
          confirmLabel={confirmMeta.confirmLabel}
          submitting={deciding}
          onConfirm={() => void applyDecision(pendingDecision)}
          onCancel={() => setPendingDecision(null)}
        />
      ) : null}
    </div>
  );
}
