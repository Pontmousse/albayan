"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import type { Document2Json } from "@drghaliasri/butex/document2";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { CompiledPdfViewer } from "@/components/dashboard/compiled-pdf-viewer";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { ExportedTexDevPanel } from "@/components/dashboard/exported-tex-dev-panel";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { SubmitDialog } from "@/components/dashboard/submit-dialog";
import { WorkflowProgress } from "@/components/dashboard/workflow-progress";
import {
  deleteArticle,
  fetchArticleAssetBlob,
  fetchDraftPdfBlob,
  fetchVersionAssetBlob,
  fetchVersionPdfBlob,
  getArticle,
  getArticleDraft,
  getDraftCompileStatus,
  getVersionDocument,
  requestDraftCompile,
  submitArticle,
  type ArticleDetail,
  updateArticle,
} from "@/lib/api/articles";
import { buttonClassName, inputClassName } from "@/lib/auth-ui";
import { ApiError } from "@/lib/api";
import { isDevMode } from "@/lib/dev-mode";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";
import { useNumerals } from "@/components/numeral-provider";
import { RECOMMENDATION_LABELS } from "@/lib/api/reviews";

export default function ArticleDetailPage() {
  const { formatDate, formatDigits } = useNumerals();
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [documentJson, setDocumentJson] = useState<
    Document2Json | null | undefined
  >(undefined);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editingMetadata, setEditingMetadata] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftAbstract, setDraftAbstract] = useState("");
  const [metadataSaving, setMetadataSaving] = useState(false);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [revisionNotice, setRevisionNotice] = useState<string | null>(null);
  const [compileStatus, setCompileStatus] = useState<
    "pending" | "processing" | "success" | "failed"
  >("pending");
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getArticle(getToken, articleId);
      setArticle(data);
      try {
        if (data.status === "draft" || data.status === "revision_requested") {
          setSelectedVersionId(null);
          const draft = await getArticleDraft(getToken, articleId);
          setDocumentJson(draft.document);
          const status = await getDraftCompileStatus(getToken, articleId);
          setCompileStatus(status.status);
        } else if (data.latest_version) {
          setSelectedVersionId(data.latest_version.id);
          const doc = await getVersionDocument(
            getToken,
            articleId,
            data.latest_version.id,
          );
          setDocumentJson(doc.document);
          setCompileStatus("success");
        } else {
          setDocumentJson(null);
        }
      } catch {
        // المعاينة اختيارية — قد يكون S3 غير مُهيّأ بعد
        setDocumentJson(null);
      }
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل المقال."));
    }
  }, [getToken, articleId]);

  const refreshStatus = useCallback(async () => {
    try {
      if (article?.status === "draft" || article?.status === "revision_requested") {
        const status = await getDraftCompileStatus(getToken, articleId);
        setCompileStatus(status.status);
      }
    } catch {
      // تجاهل أخطاء الاستطلاع المؤقتة
    }
  }, [getToken, articleId, article?.status]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSubmit() {
    setSubmitting(true);
    setSubmitError(null);
    try {
      await submitArticle(getToken, articleId);
      setDialogOpen(false);
      await load();
    } catch (err) {
      setSubmitError(userFacingErrorMessage(err, "تعذّر تقديم المقال."));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setSubmitError(null);
    try {
      await deleteArticle(getToken, articleId);
      setDeleteDialogOpen(false);
      router.push("/maktabi/maqalati");
    } catch (err) {
      setSubmitError(userFacingErrorMessage(err, "تعذّر حذف المسودة."));
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  }

  function beginMetadataEdit() {
    if (!article) return;
    setDraftTitle(article.title);
    setDraftAbstract(article.abstract ?? "");
    setMetadataError(null);
    setEditingMetadata(true);
  }

  function cancelMetadataEdit() {
    if (metadataSaving) return;
    setEditingMetadata(false);
    setMetadataError(null);
  }

  async function handleMetadataSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = draftTitle.trim();
    if (!title) {
      setMetadataError("عنوان المقال مطلوب.");
      return;
    }

    setMetadataSaving(true);
    setMetadataError(null);
    try {
      const updated = await updateArticle(getToken, articleId, {
        base_revision: article?.draft_revision_number ?? 0,
        title,
        abstract: draftAbstract.trim() || null,
      });
      setArticle(updated);
      setEditingMetadata(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        await load();
        setEditingMetadata(false);
        setRevisionNotice(
          "وصلت تعديلات أحدث من مصدر آخر؛ حُمّلت أحدث مسودة من الخادم.",
        );
        return;
      }
      setMetadataError(
        userFacingErrorMessage(err, "تعذّر حفظ بيانات المسودة."),
      );
    } finally {
      setMetadataSaving(false);
    }
  }

  async function handleCompile() {
    const status = await requestDraftCompile(getToken, articleId);
    setCompileStatus(status.status);
  }

  const fetchPdfBlob = useCallback(
    (tokenGetter: typeof getToken) => {
      if (!selectedVersionId && (article?.status === "draft" || article?.status === "revision_requested")) {
        return fetchDraftPdfBlob(tokenGetter, articleId);
      }
      const versionId = selectedVersionId ?? article?.latest_version?.id;
      if (!versionId) {
        return Promise.reject(new Error("لا يوجد إصدار رسمي للمقال."));
      }
      return fetchVersionPdfBlob(tokenGetter, articleId, versionId);
    },
    [article, articleId, selectedVersionId],
  );

  const fetchPreviewAsset = useCallback(
    (tokenGetter: typeof getToken, _scopeId: string, assetKey: string) => {
      if (!selectedVersionId) {
        return fetchArticleAssetBlob(tokenGetter, articleId, assetKey);
      }
      return fetchVersionAssetBlob(tokenGetter, articleId, selectedVersionId, assetKey);
    },
    [articleId, selectedVersionId],
  );

  async function selectVersion(versionId: string) {
    setSelectedVersionId(versionId);
    setDocumentJson(undefined);
    try {
      const payload = await getVersionDocument(getToken, articleId, versionId);
      setDocumentJson(payload.document);
      setCompileStatus("success");
    } catch {
      setDocumentJson(null);
    }
  }

  async function showCurrentDraft() {
    setSelectedVersionId(null);
    const payload = await getArticleDraft(getToken, articleId);
    setDocumentJson(payload.document);
    const status = await getDraftCompileStatus(getToken, articleId);
    setCompileStatus(status.status);
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
          onClick={() => router.push("/maktabi/maqalati")}
          className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          العودة إلى مقالاتي
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

  const isDraft = article.status === "draft";
  const isRevisionRound = article.status === "revision_requested";
  const isEditable = isDraft || isRevisionRound;

  return (
    <div className="space-y-8">
      {revisionNotice ? (
        <p
          className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
          role="alert"
        >
          {revisionNotice}
        </p>
      ) : null}
      <div>
        <Link
          href="/maktabi/maqalati"
          className="text-xs font-medium text-slate-500 underline-offset-4 hover:text-[var(--journal-accent)] hover:underline"
        >
          → مقالاتي
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1
                className="text-2xl font-bold leading-relaxed text-slate-900 sm:text-3xl"
                style={{ fontFamily: "var(--font-display-ar), serif" }}
              >
                {article.title}
              </h1>
              {isEditable && !editingMetadata ? (
                <button
                  type="button"
                  onClick={beginMetadataEdit}
                  className="rounded-md border border-[var(--journal-border)] bg-white px-2.5 py-1 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent)]"
                >
                  تعديل البيانات
                </button>
              ) : null}
            </div>
            <p className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-slate-500">
              <StatusBadge status={article.status} />
              <span>
                {article.latest_version
                  ? `الإصدار ${formatDigits(article.latest_version.version_number)}`
                  : `مراجعة المسودة ${formatDigits(article.draft_revision_number)}`}
              </span>
              <span aria-hidden>·</span>
              <span>أُنشئ في {formatDate(article.created_at)}</span>
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2.5">
            {isEditable ? (
              <>
                <Link
                  href={`/maktabi/maqalati/${article.id}/tahrir`}
                  className={buttonClassName}
                >
                  {isRevisionRound ? "متابعة التعديل" : "متابعة التحرير"}
                </Link>
                <button
                  type="button"
                  onClick={() => setDialogOpen(true)}
                  className="rounded-md border border-[var(--journal-gold)] bg-white px-5 py-2.5 text-sm font-semibold text-[var(--journal-gold)] transition hover:bg-[var(--journal-accent-soft)]"
                >
                  {isRevisionRound ? "إعادة تقديم المقال" : "تقديم المقال"}
                </button>
                {isDraft ? <button
                  type="button"
                  onClick={() => setDeleteDialogOpen(true)}
                  className="rounded-md border border-red-300 bg-white px-5 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-50"
                >
                  حذف المسودة
                </button> : null}
              </>
            ) : null}
          </div>
        </div>
        {editingMetadata ? (
          <form
            onSubmit={handleMetadataSave}
            className="mt-5 space-y-4 rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm"
          >
            <div>
              <label
                htmlFor="draft-title"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                عنوان المقال <span className="text-red-600">*</span>
              </label>
              <input
                id="draft-title"
                type="text"
                required
                maxLength={500}
                value={draftTitle}
                onChange={(event) => setDraftTitle(event.target.value)}
                className={inputClassName}
                disabled={metadataSaving}
              />
            </div>
            <div>
              <label
                htmlFor="draft-abstract"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                الملخص <span className="text-xs text-slate-400">(اختياري)</span>
              </label>
              <textarea
                id="draft-abstract"
                rows={5}
                maxLength={5000}
                value={draftAbstract}
                onChange={(event) => setDraftAbstract(event.target.value)}
                className={inputClassName}
                disabled={metadataSaving}
              />
            </div>
            {metadataError ? (
              <p
                className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                role="alert"
              >
                {metadataError}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2.5">
              <button
                type="submit"
                disabled={metadataSaving || !draftTitle.trim()}
                className={`${buttonClassName} disabled:cursor-not-allowed disabled:opacity-60`}
              >
                {metadataSaving ? "جارٍ الحفظ…" : "حفظ البيانات"}
              </button>
              <button
                type="button"
                onClick={cancelMetadataEdit}
                disabled={metadataSaving}
                className="rounded-md border border-[var(--journal-border)] bg-white px-5 py-2.5 text-sm font-semibold text-slate-600 transition hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                إلغاء
              </button>
            </div>
          </form>
        ) : null}
      </div>

      {submitError ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {submitError}
        </p>
      ) : null}

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">مسار المخطوطة</h2>
        <div className="mt-3">
          <WorkflowProgress status={article.status} />
        </div>
        {!isEditable ? (
          <p className="mt-3 text-xs leading-6 text-slate-500">
            المخطوطة مجمّدة — لا يمكن تعديل المحتوى في هذه المرحلة.
          </p>
        ) : null}
      </section>

      {isEditable || article.abstract ? (
        <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-[var(--journal-accent)]">الملخص</h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">
            {article.abstract || "لا يوجد ملخص لبيانات المسودة بعد."}
          </p>
        </section>
      ) : null}

      {isRevisionRound ? (
        <section className="rounded-xl border border-amber-300 bg-amber-50 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-amber-950">مطلوب تعديل</h2>
          {article.revision_requested_at ? (
            <p className="mt-1 text-xs text-amber-800">
              طُلب في {formatDate(article.revision_requested_at)}
            </p>
          ) : null}
          <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-amber-950">
            {article.revision_request_note}
          </p>
          {article.revision_feedback.length ? (
            <ul className="mt-4 space-y-3">
              {article.revision_feedback.map((feedback) => (
                <li key={feedback.review_id} className="rounded-lg border border-amber-200 bg-white p-3 text-sm">
                  <p className="font-semibold text-slate-800">{feedback.reviewer_label}</p>
                  {feedback.recommendation ? (
                    <p className="mt-1 text-xs text-slate-500">
                      التوصية: {RECOMMENDATION_LABELS[feedback.recommendation]}
                    </p>
                  ) : null}
                  <p className="mt-1 whitespace-pre-wrap leading-6 text-slate-700">{feedback.comments_to_author}</p>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

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
                <span className="text-xs text-slate-500">{version.title_snapshot}</span>
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
                  {selectedVersionId === version.id ? "معروض الآن" : "عرض النسخة"}
                </button>
              </span>
            </li>
          ))}
        </ul>
        {isEditable && selectedVersionId ? (
          <button
            type="button"
            onClick={() => void showCurrentDraft()}
            className="mt-3 text-xs font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
          >
            العودة إلى مسودة التعديل الحالية
          </button>
        ) : null}
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
            fetchAssetBlob={fetchPreviewAsset}
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
            compileStatus={compileStatus}
            getToken={getToken}
            scopeId={articleId}
            fetchPdfBlob={fetchPdfBlob}
            onRequestCompile={isEditable && !selectedVersionId ? handleCompile : undefined}
            onRefreshStatus={isEditable && !selectedVersionId ? refreshStatus : undefined}
          />
          {isDevMode() ? (
            <ExportedTexDevPanel
              documentJson={documentJson}
              compileStatus={compileStatus}
              articleId={articleId}
              getToken={getToken}
            />
          ) : null}
        </div>
      </section>

      <SubmitDialog
        open={dialogOpen}
        submitting={submitting}
        onConfirm={handleSubmit}
        onCancel={() => setDialogOpen(false)}
        resubmission={isRevisionRound}
      />

      <ConfirmDialog
        open={deleteDialogOpen}
        title="حذف المسودة"
        description="حذف هذه المسودة نهائياً مع المخطوطة والصور وملف المعاينة؟ لا يمكن التراجع."
        confirmLabel="حذف نهائياً"
        submitting={deleting}
        onConfirm={() => void handleDelete()}
        onCancel={() => {
          if (!deleting) setDeleteDialogOpen(false);
        }}
      />
    </div>
  );
}
