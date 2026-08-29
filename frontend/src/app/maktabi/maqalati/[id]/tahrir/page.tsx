"use client";

import { useAuth } from "@clerk/nextjs";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ComponentType,
  type Ref,
} from "react";
import type { Document2Json } from "@drghaliasri/butex/document2";
import type {
  ButexDocumentEditor2Props,
  ButexDocumentEditor2Ref,
} from "@drghaliasri/butex/react-document2";
import { ArticleAssetsPanel } from "@/components/dashboard/article-assets-panel";
import { DocumentJsonDevDialog } from "@/components/dashboard/document-json-dev-dialog";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import { SubmitDialog } from "@/components/dashboard/submit-dialog";
import {
  getArticle,
  getArticleSession,
  saveArticleSession,
  submitArticle,
  updateArticleSessionDocument,
  type ArticleDetail,
} from "@/lib/api/articles";
import { useButexImageResolver } from "@/lib/butex-images";
import { ensureButexMathJax } from "@/lib/butex-mathjax";
import { ALBAYAN_BUTEX_THEME_CLASS } from "@/lib/butex-theme";
import { isDevMode } from "@/lib/dev-mode";

type EditorPhase = "loading" | "ready" | "blocked";

const ButexDocumentEditor2 = dynamic(
  () =>
    import("@drghaliasri/butex/react-document2").then(
      (mod) => mod.ButexDocumentEditor2,
    ),
  { ssr: false },
);

const ButexDocumentEditor2WithRef = ButexDocumentEditor2 as ComponentType<
  ButexDocumentEditor2Props & {
    ref?: Ref<ButexDocumentEditor2Ref>;
  }
>;

export default function TahrirPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [phase, setPhase] = useState<EditorPhase>("loading");
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [initialDocument, setInitialDocument] = useState<
    Document2Json | undefined
  >(undefined);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [assetsPanelOpen, setAssetsPanelOpen] = useState(false);
  const [assetsUploading, setAssetsUploading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [jsonDialogOpen, setJsonDialogOpen] = useState(false);
  /** لقطة JSON قانونية مطابقة لما يُرسل إلى API — للوحة DEV فقط. */
  const [liveDocument, setLiveDocument] = useState<Document2Json | null>(null);

  const latestDocumentJson = useRef<Document2Json | null>(null);
  const savedDocumentSnapshot = useRef<string | null>(null);
  const sessionRevision = useRef(0);
  const sessionNeedsDraftSave = useRef(false);
  const editorRef = useRef<ButexDocumentEditor2Ref>(null);
  const editorRootRef = useRef<HTMLDivElement>(null);
  const actionBarRef = useRef<HTMLDivElement>(null);
  const showDevJson = isDevMode();

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

        const payload = await getArticleSession(getToken, articleId);
        const doc = payload.document;
        const revision = payload.revision;
        const lastSavedRevision = payload.last_saved_revision;
        if (cancelled) return;

        await ensureButexMathJax();
        if (cancelled) return;

        latestDocumentJson.current = doc;
        savedDocumentSnapshot.current = null;
        sessionRevision.current = revision;
        sessionNeedsDraftSave.current = revision > lastSavedRevision;
        setInitialDocument(doc ?? undefined);
        if (isDevMode()) {
          setLiveDocument(doc);
        }
        if (doc) prefetchFromDocument(doc);
        if (revision > lastSavedRevision) {
          setDirty(true);
          setSaveMessage("توجد تعديلات في جلسة التحرير لم تُحفظ في نسخة المقال بعد.");
        }
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
    const root = editorRootRef.current;
    const actionBar = actionBarRef.current;
    const siteHeader = document.querySelector<HTMLElement>("[data-site-header]");
    if (!root || !actionBar) return;

    const updateStickyOffsets = () => {
      root.style.setProperty(
        "--article-editor-site-header-height",
        `${siteHeader?.getBoundingClientRect().height ?? 0}px`,
      );
      root.style.setProperty(
        "--article-editor-actions-height",
        `${actionBar.getBoundingClientRect().height}px`,
      );
    };

    updateStickyOffsets();
    const observer = new ResizeObserver(updateStickyOffsets);
    observer.observe(actionBar);
    if (siteHeader) observer.observe(siteHeader);
    window.addEventListener("resize", updateStickyOffsets);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateStickyOffsets);
    };
  }, []);

  useEffect(() => {
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (dirty) event.preventDefault();
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty]);

  const handleDocumentJsonChange = useCallback(
    (doc: Document2Json) => {
      latestDocumentJson.current = doc;
      const snapshot = JSON.stringify(doc);

      if (savedDocumentSnapshot.current === null) {
        savedDocumentSnapshot.current = snapshot;
        setDirty(sessionNeedsDraftSave.current);
      } else {
        const changed = snapshot !== savedDocumentSnapshot.current;
        setDirty(changed || sessionNeedsDraftSave.current);
        if (changed) setSaveMessage(null);
      }

      prefetchFromDocument(doc);
      if (isDevMode()) setLiveDocument(doc);
    },
    [prefetchFromDocument],
  );

  async function handleSave(): Promise<boolean> {
    if (!latestDocumentJson.current) {
      setSaveMessage("لا تغييرات للحفظ.");
      return true;
    }
    const documentToSave = latestDocumentJson.current;
    const snapshotToSave = JSON.stringify(documentToSave);
    setSaving(true);
    setError(null);
    try {
      if (snapshotToSave !== savedDocumentSnapshot.current) {
        const session = await updateArticleSessionDocument(
          getToken,
          articleId,
          documentToSave,
          sessionRevision.current,
        );
        sessionRevision.current = session.revision;
        sessionNeedsDraftSave.current =
          session.revision > session.last_saved_revision;
        savedDocumentSnapshot.current = JSON.stringify(session.document);
      }

      const saved = await saveArticleSession(getToken, articleId);
      sessionRevision.current = saved.revision;
      sessionNeedsDraftSave.current =
        saved.revision > saved.last_saved_revision;
      savedDocumentSnapshot.current = snapshotToSave;

      const currentSnapshot = latestDocumentJson.current
        ? JSON.stringify(latestDocumentJson.current)
        : snapshotToSave;
      const changedWhileSaving = currentSnapshot !== snapshotToSave;
      setDirty(changedWhileSaving || sessionNeedsDraftSave.current);
      setSaveMessage(
        changedWhileSaving
          ? "تم حفظ النسخة السابقة — توجد تغييرات أحدث غير محفوظة."
          : "تم الحفظ.",
      );
      if (changedWhileSaving) {
        setError("تغيّر المستند أثناء الحفظ؛ احفظ التغييرات الأحدث قبل التقديم.");
      }
      return !changedWhileSaving;
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

  const handleInsertFigure = useCallback(
    async (assetId: string) => {
      if (phase !== "ready") return;
      setError(null);
      try {
        await ensureAsset(assetId);
        editorRef.current?.insertImageBlock?.(assetId);
        setSaveMessage("أُدرجت الصورة في المستند — احفظ المخطوطة.");
      } catch (err) {
        setError(err instanceof Error ? err.message : "تعذّر إدراج الصورة.");
      }
    },
    [ensureAsset, phase],
  );

  return (
    <div
      ref={editorRootRef}
      className="article-editor flex flex-1 flex-col bg-[var(--journal-paper)]"
    >
      <div
        ref={actionBarRef}
        className="article-editor__actions sticky z-30 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 backdrop-blur-sm"
      >
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
            {showDevJson ? (
              <button
                type="button"
                onClick={() => setJsonDialogOpen(true)}
                disabled={phase !== "ready"}
                className="min-h-9 rounded-md border border-amber-400 bg-amber-50 px-4 py-1.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                See JSON
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => setAssetsPanelOpen(true)}
              disabled={assetsUploading || phase !== "ready"}
              className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-4 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {assetsUploading ? "جارٍ الرفع…" : "صور المقال"}
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
          <ButexDocumentEditor2WithRef
            ref={editorRef}
            className={ALBAYAN_BUTEX_THEME_CLASS}
            initialDocument={initialDocument}
            uiLocale="ar"
            documentDirection="rtl"
            equationSide="arabic"
            mathOutput="svg"
            editableEquations
            resolveImageUrl={resolveImageUrl}
            onDocumentJsonChange={handleDocumentJsonChange}
          />
        ) : null}
      </main>

      <SubmitDialog
        open={dialogOpen}
        submitting={submitting}
        onConfirm={handleSubmit}
        onCancel={() => setDialogOpen(false)}
      />

      {showDevJson ? (
        <DocumentJsonDevDialog
          open={jsonDialogOpen}
          value={liveDocument}
          onClose={() => setJsonDialogOpen(false)}
        />
      ) : null}

      <ArticleAssetsPanel
        open={assetsPanelOpen}
        articleId={articleId}
        getToken={getToken}
        resolveImageUrl={resolveImageUrl}
        ensureAsset={ensureAsset}
        onClose={() => setAssetsPanelOpen(false)}
        onInsertFigure={(assetId) => void handleInsertFigure(assetId)}
        onUploadingChange={setAssetsUploading}
      />
    </div>
  );
}
