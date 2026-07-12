"use client";

import { useAuth } from "@clerk/nextjs";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  addDocument2ImageBlock,
  createEmptyDocument2,
  type Document2Node,
} from "@drghaliasri/butex/document2";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import { SubmitDialog } from "@/components/dashboard/submit-dialog";
import {
  getArticle,
  getArticleDocument,
  saveArticleDocument,
  submitArticle,
  uploadArticleAsset,
  type ArticleDetail,
} from "@/lib/api/articles";
import { useButexImageResolver } from "@/lib/butex-images";
import { ensureButexMathJax } from "@/lib/butex-mathjax";
import { ALBAYAN_BUTEX_THEME_CLASS } from "@/lib/butex-theme";

const ButexDocumentEditor2 = dynamic(
  () =>
    import("@drghaliasri/butex/react-document2").then(
      (mod) => mod.ButexDocumentEditor2,
    ),
  { ssr: false },
);

type EditorPhase = "loading" | "ready" | "blocked";

export default function TahrirPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [phase, setPhase] = useState<EditorPhase>("loading");
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [initialDocument, setInitialDocument] = useState<unknown>(undefined);
  const [editorKey, setEditorKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const latestDocument = useRef<Document2Node | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { resolveImageUrl, prefetchFromDocument, ensureAsset } =
    useButexImageResolver(articleId, getToken);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        const data = await getArticle(getToken, articleId);
        if (cancelled) return;

        if (data.current_version.status !== "draft") {
          // المخطوطة مجمّدة — لا محرر
          router.replace(`/maktabi/maqalati/${articleId}`);
          setPhase("blocked");
          return;
        }

        setArticle(data);

        let doc: unknown = null;
        try {
          const payload = await getArticleDocument(getToken, articleId);
          doc = payload.document;
        } catch {
          // أول فتح أو S3 غير مُهيّأ — نبدأ بمستند فارغ
          doc = null;
        }
        if (cancelled) return;

        await ensureButexMathJax();
        if (cancelled) return;

        setInitialDocument(doc ?? undefined);
        if (doc) prefetchFromDocument(doc);
        setPhase("ready");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر فتح المحرر.");
        }
      }
    }

    void boot();
    return () => {
      cancelled = true;
    };
  }, [getToken, articleId, router, prefetchFromDocument]);

  useEffect(() => {
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (dirty) event.preventDefault();
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty]);

  const handleDocumentChange = useCallback(
    (doc: Document2Node) => {
      latestDocument.current = doc;
      setDirty(true);
      setSaveMessage(null);
      prefetchFromDocument(doc);
    },
    [prefetchFromDocument],
  );

  async function handleSave(): Promise<boolean> {
    if (!latestDocument.current) {
      setSaveMessage("لا تغييرات للحفظ.");
      return true;
    }
    setSaving(true);
    setError(null);
    try {
      await saveArticleDocument(getToken, articleId, latestDocument.current);
      setDirty(false);
      setSaveMessage("تم الحفظ.");
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر حفظ المخطوطة.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    setSubmitting(true);
    try {
      if (dirty) {
        const saved = await handleSave();
        if (!saved) {
          setSubmitting(false);
          setDialogOpen(false);
          return;
        }
      }
      await submitArticle(getToken, articleId);
      setDirty(false);
      router.push(`/maktabi/maqalati/${articleId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تقديم المقال.");
      setSubmitting(false);
      setDialogOpen(false);
    }
  }

  function handleBack() {
    if (dirty && !window.confirm("لديك تغييرات غير محفوظة — هل تريد المغادرة؟")) {
      return;
    }
    router.push(`/maktabi/maqalati/${articleId}`);
  }

  async function handleImageFile(file: File | undefined) {
    if (!file || phase !== "ready") return;
    setUploading(true);
    setError(null);
    try {
      const { asset_id } = await uploadArticleAsset(getToken, articleId, file);
      await ensureAsset(asset_id);

      const base = latestDocument.current ?? createEmptyDocument2();
      const next = addDocument2ImageBlock(base, asset_id);
      latestDocument.current = next;
      setInitialDocument(next);
      setEditorKey((k) => k + 1);
      setDirty(true);
      setSaveMessage("أُدرجت الصورة — احفظ المخطوطة.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر رفع الصورة.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <div className="sticky top-0 z-40 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={handleBack}
              className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
            >
              → رجوع
            </button>
            <h1
              className="min-w-0 truncate text-base font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              {article?.title ?? "المحرر"}
            </h1>
          </div>
          <div className="flex items-center gap-2.5">
            {saveMessage ? (
              <span className="text-xs text-emerald-700" role="status">
                {saveMessage}
              </span>
            ) : dirty ? (
              <span className="text-xs text-[var(--journal-gold)]">
                تغييرات غير محفوظة
              </span>
            ) : null}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              className="sr-only"
              onChange={(event) =>
                void handleImageFile(event.target.files?.[0])
              }
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading || phase !== "ready"}
              className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-4 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {uploading ? "جارٍ الرفع…" : "رفع صورة"}
            </button>
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving || phase !== "ready"}
              className="min-h-9 rounded-md bg-[var(--journal-accent)] px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "جارٍ الحفظ…" : "حفظ"}
            </button>
            <button
              type="button"
              onClick={() => setDialogOpen(true)}
              disabled={phase !== "ready"}
              className="min-h-9 rounded-md border border-[var(--journal-gold)] bg-white px-4 py-1.5 text-xs font-semibold text-[var(--journal-gold)] transition hover:bg-[var(--journal-accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              تقديم
            </button>
          </div>
        </div>
      </div>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {error ? (
          <p
            className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        {phase === "loading" && !error ? (
          <div className="space-y-4">
            <SkeletonBlock className="h-12" />
            <SkeletonBlock className="h-64" />
            <p className="text-center text-sm text-slate-500">
              جارٍ تحميل المحرر وتهيئة عرض المعادلات…
            </p>
          </div>
        ) : null}

        {phase === "ready" ? (
          <ButexDocumentEditor2
            key={editorKey}
            className={ALBAYAN_BUTEX_THEME_CLASS}
            initialDocument={
              initialDocument as
                | import("@drghaliasri/butex/document2").Document2Json
                | Document2Node
                | undefined
            }
            uiLocale="ar"
            documentDirection="rtl"
            equationSide="arabic"
            mathOutput="svg"
            editableEquations
            resolveImageUrl={resolveImageUrl}
            onDocumentChange={handleDocumentChange}
          />
        ) : null}
      </main>

      <SubmitDialog
        open={dialogOpen}
        submitting={submitting}
        onConfirm={handleSubmit}
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  );
}
