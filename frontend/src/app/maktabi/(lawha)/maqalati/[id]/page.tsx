"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { CompiledPdfViewer } from "@/components/dashboard/compiled-pdf-viewer";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { SubmitDialog } from "@/components/dashboard/submit-dialog";
import { WorkflowProgress } from "@/components/dashboard/workflow-progress";
import {
  fetchArticlePdfBlob,
  getArticle,
  getArticleDocument,
  requestArticleCompile,
  submitArticle,
  type ArticleDetail,
} from "@/lib/api/articles";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

export default function ArticleDetailPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [documentJson, setDocumentJson] = useState<unknown>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getArticle(getToken, articleId);
      setArticle(data);
      try {
        const doc = await getArticleDocument(getToken, articleId);
        setDocumentJson(doc.document);
      } catch {
        // المعاينة اختيارية — قد يكون S3 غير مُهيّأ بعد
        setDocumentJson(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل المقال.");
    }
  }, [getToken, articleId]);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await getArticle(getToken, articleId);
      setArticle(data);
    } catch {
      // تجاهل أخطاء الاستطلاع المؤقتة
    }
  }, [getToken, articleId]);

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
      setSubmitError(err instanceof Error ? err.message : "تعذّر تقديم المقال.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCompile() {
    const version = await requestArticleCompile(getToken, articleId);
    setArticle((prev) =>
      prev
        ? {
            ...prev,
            current_version: version,
            versions: prev.versions.map((v) =>
              v.id === version.id ? version : v,
            ),
          }
        : prev,
    );
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

  const current = article.current_version;
  const isDraft = current.status === "draft";

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/maktabi/maqalati"
          className="text-xs font-medium text-slate-500 underline-offset-4 hover:text-[var(--journal-accent)] hover:underline"
        >
          → مقالاتي
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
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
          <div className="flex shrink-0 flex-wrap gap-2.5">
            {isDraft ? (
              <>
                <Link
                  href={`/maktabi/maqalati/${article.id}/tahrir`}
                  className={buttonClassName}
                >
                  متابعة التحرير
                </Link>
                <button
                  type="button"
                  onClick={() => setDialogOpen(true)}
                  className="rounded-md border border-[var(--journal-gold)] bg-white px-5 py-2.5 text-sm font-semibold text-[var(--journal-gold)] transition hover:bg-[var(--journal-accent-soft)]"
                >
                  تقديم المقال
                </button>
              </>
            ) : null}
          </div>
        </div>
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
          <WorkflowProgress status={current.status} />
        </div>
        {!isDraft ? (
          <p className="mt-3 text-xs leading-6 text-slate-500">
            المخطوطة مجمّدة — لا يمكن تعديل المحتوى في هذه المرحلة.
          </p>
        ) : null}
      </section>

      {article.abstract ? (
        <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-[var(--journal-accent)]">الملخص</h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">{article.abstract}</p>
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
          />
        </div>
      </section>

      <section>
        <h2
          className="text-lg font-bold text-[var(--journal-accent)]"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          معاينة PDF
        </h2>
        <div className="mt-3">
          <CompiledPdfViewer
            compileStatus={current.compile_status}
            getToken={getToken}
            scopeId={articleId}
            fetchPdfBlob={fetchArticlePdfBlob}
            onRequestCompile={handleCompile}
            onRefreshStatus={refreshStatus}
          />
        </div>
      </section>

      <SubmitDialog
        open={dialogOpen}
        submitting={submitting}
        onConfirm={handleSubmit}
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  );
}
