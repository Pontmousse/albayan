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
import { useNumerals } from "@/components/numeral-provider";
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
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

const DECISIONS: {
  status: EditorDecisionStatus;
  label: string;
  needsConfirm: boolean;
}[] = [
  { status: "under_review", label: "قيد المراجعة", needsConfirm: false },
  { status: "revision_requested", label: "طلب تعديلات", needsConfirm: false },
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
  const { formatDate, formatDigits } = useNumerals();
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
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [disclosures, setDisclosures] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      const data = await getEditorArticle(getToken, articleId);
      setArticle(data);
      setSelectedVersionId(data.latest_version.id);
      setDisclosures(Object.fromEntries(data.reviews.map((review) => [
        review.id,
        review.reveal_reviewer_identity_to_author,
      ])));
      try {
        const doc = await getEditorDocument(
          getToken,
          articleId,
          data.latest_version.id,
        );
        setDocumentJson(doc.document);
      } catch {
        setDocumentJson(null);
      }
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل المقال."));
    }
  }, [getToken, articleId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function applyDecision(status: EditorDecisionStatus) {
    if (status === "revision_requested" && !reason.trim()) {
      setDecisionError("اكتب توجيهات التعديل قبل إرسال الطلب للمؤلف.");
      return;
    }
    setDeciding(true);
    setDecisionError(null);
    setDecisionOk(null);
    try {
      await postEditorDecision(
        getToken,
        articleId,
        status,
        reason.trim() || null,
        status === "revision_requested"
          ? article?.reviews.map((review) => ({
              review_id: review.id,
              reveal_identity: disclosures[review.id] ?? false,
            })) ?? []
          : [],
      );
      setPendingDecision(null);
      setDecisionOk("تم تحديث القرار التحريري.");
      await load();
    } catch (err) {
      setDecisionError(userFacingErrorMessage(err, "تعذّر تحديث القرار."));
    } finally {
      setDeciding(false);
    }
  }

  async function selectVersion(versionId: string) {
    setSelectedVersionId(versionId);
    setDocumentJson(undefined);
    try {
      const doc = await getEditorDocument(getToken, articleId, versionId);
      setDocumentJson(doc.document);
    } catch {
      setDocumentJson(null);
    }
  }

  const fetchSelectedAsset = useCallback(
    (tokenGetter: typeof getToken, _scopeId: string, assetKey: string) => {
      if (!selectedVersionId) return Promise.reject(new Error("لا يوجد إصدار محدد."));
      return fetchEditorAssetBlob(tokenGetter, articleId, selectedVersionId, assetKey);
    },
    [articleId, selectedVersionId],
  );

  const fetchSelectedPdf = useCallback(
    (tokenGetter: typeof getToken) => {
      if (!selectedVersionId) return Promise.reject(new Error("لا يوجد إصدار محدد."));
      return fetchEditorPdfBlob(tokenGetter, articleId, selectedVersionId);
    },
    [articleId, selectedVersionId],
  );

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

  const latest = article.latest_version;
  const selectedVersion = article.versions.find((version) => version.id === selectedVersionId) ?? latest;
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
            <StatusBadge status={article.status} />
            <span>الإصدار {formatDigits(latest.version_number)}</span>
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
          <WorkflowProgress status={article.status} />
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
                  الإصدار {formatDigits(version.version_number)}
                </span>
              </span>
              <span className="flex items-center gap-3 text-xs text-slate-500">
                {version.submitted_at
                  ? `قُدِّم في ${formatDate(version.submitted_at)}`
                  : `أُنشئ في ${formatDate(version.created_at)}`}
                <button
                  type="button"
                  onClick={() => void selectVersion(version.id)}
                  className="font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
                >
                  {selectedVersion.id === version.id ? "معروض الآن" : "عرض المخطوطة"}
                </button>
              </span>
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
            fetchAssetBlob={fetchSelectedAsset}
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
            compileStatus="success"
            getToken={getToken}
            scopeId={articleId}
            fetchPdfBlob={fetchSelectedPdf}
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
                <label className="mt-3 flex items-center gap-2 text-xs font-medium text-slate-700">
                  <input
                    type="checkbox"
                    checked={disclosures[review.id] ?? false}
                    onChange={(event) => setDisclosures((current) => ({
                      ...current,
                      [review.id]: event.target.checked,
                    }))}
                  />
                  إظهار اسم هذا المراجع للمؤلف عند طلب التعديلات
                </label>
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
            توجيهات القرار (مطلوبة عند طلب التعديلات)
          </span>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            maxLength={2000}
            className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
            placeholder="اشرح للمؤلف ما المطلوب تعديله."
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2.5">
          {DECISIONS.map((item) => (
            <button
              key={item.status}
              type="button"
              disabled={
                deciding ||
                article.status === item.status ||
                !(
                  (article.status === "submitted" && ["under_review", "revision_requested", "accepted", "rejected"].includes(item.status)) ||
                  (article.status === "under_review" && ["revision_requested", "accepted", "rejected"].includes(item.status))
                )
              }
              onClick={() =>
                handleDecisionClick(item.status, item.needsConfirm)
              }
              className={
                article.status === item.status
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
