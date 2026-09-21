"use client";

import { useAuth } from "@clerk/nextjs";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Document2Json } from "@drghaliasri/butex/document2";
import type { ImageAssetRef } from "@drghaliasri/butex/react-document2";
import {
  ArticleAssetsPanel,
  type ArticleAssetsPanelMode,
} from "@/components/dashboard/article-assets-panel";
import { ArticleEditorHeader } from "@/components/dashboard/article-editor-header";
import { DocumentJsonDevDialog } from "@/components/dashboard/document-json-dev-dialog";
import { DraftHistoryDialog } from "@/components/dashboard/draft-history-dialog";
import { EquationMappingsPanel } from "@/components/dashboard/equation-mappings-panel";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import { SubmitDialog } from "@/components/dashboard/submit-dialog";
import { useNumerals } from "@/components/numeral-provider";
import {
  getArticle,
  getArticleDraft,
  listArticleAssets,
  putArticleDraft,
  restoreDraftRevision,
  submitArticle,
  type ArticleDetail,
  type DraftRevision,
  type DraftRevisionHistoryItem,
} from "@/lib/api/articles";
import { ApiError } from "@/lib/api";
import {
  DraftAutosaveController,
} from "@/lib/draft-autosave";
import { createButexImageAssetListCache } from "@/lib/butex-image-assets";
import { useButexImageResolver } from "@/lib/butex-images";
import { ensureButexMathJax } from "@/lib/butex-mathjax";
import { ALBAYAN_BUTEX_THEME_CLASS } from "@/lib/butex-theme";
import { isButexDocumentValid } from "@/lib/butex-validation";
import { isDevMode } from "@/lib/dev-mode";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

type EditorPhase = "loading" | "ready" | "blocked";

const ButexDocumentEditor2 = dynamic(
  () =>
    import("@drghaliasri/butex/react-document2").then(
      (mod) => mod.ButexDocumentEditor2,
    ),
  { ssr: false },
);

export default function TahrirPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { formatDigits } = useNumerals();
  const articleId = params.id;

  const [phase, setPhase] = useState<EditorPhase>("loading");
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [initialDocument, setInitialDocument] = useState<
    Document2Json | undefined
  >(undefined);
  const [error, setError] = useState<string | null>(null);
  const [assetListError, setAssetListError] = useState<string | null>(null);
  const [assetListRetrying, setAssetListRetrying] = useState(false);
  const [assetListRevision, setAssetListRevision] = useState(0);
  const [assetsPanelMode, setAssetsPanelMode] =
    useState<ArticleAssetsPanelMode | null>(null);
  const [pickerCurrentAssetId, setPickerCurrentAssetId] = useState<
    string | null
  >(null);
  const [assetsUploading, setAssetsUploading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveFailed, setSaveFailed] = useState(false);
  const [conflictNotice, setConflictNotice] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [editorKey, setEditorKey] = useState(0);
  const [documentValid, setDocumentValid] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [jsonDialogOpen, setJsonDialogOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [equationMappingsOpen, setEquationMappingsOpen] = useState(false);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  /** لقطة JSON قانونية مطابقة لما يُرسل إلى API — للوحة DEV فقط. */
  const [liveDocument, setLiveDocument] = useState<Document2Json | null>(null);

  const latestDocumentJson = useRef<Document2Json | null>(null);
  const autosaveController = useRef<DraftAutosaveController | null>(null);
  const editorRootRef = useRef<HTMLDivElement>(null);
  const actionBarRef = useRef<HTMLDivElement>(null);
  const pendingImagePickRef = useRef<
    ((asset: ImageAssetRef | null) => void) | null
  >(null);
  const assetsPanelReturnFocusRef = useRef<HTMLElement | null>(null);
  const showDevJson = isDevMode();

  const { resolveImageUrl, prefetchFromDocument, ensureAsset } =
    useButexImageResolver(articleId, getToken);

  const syncVisibleMetadata = useCallback((doc: Document2Json) => {
    const meta = doc.meta;
    if (!meta || typeof meta.title !== "string") return;
    setArticle((current) => current ? {
      ...current,
      title: meta.title,
      abstract: typeof meta.abstract === "string" ? meta.abstract || null : current.abstract,
    } : current);
  }, []);

  const applyRevisionToEditor = useCallback((revision: DraftRevision) => {
    latestDocumentJson.current = revision.document;
    syncVisibleMetadata(revision.document);
    setInitialDocument(revision.document);
    setEditorKey((key) => key + 1);
    setDocumentValid(isButexDocumentValid(revision.document));
    if (isDevMode()) setLiveDocument(revision.document);
    prefetchFromDocument(revision.document);
  }, [prefetchFromDocument, syncVisibleMetadata]);

  const installAutosaveController = useCallback((initial: DraftRevision) => {
    autosaveController.current?.dispose();
    autosaveController.current = new DraftAutosaveController({
      initial,
      save: (document, baseRevision) =>
        putArticleDraft(getToken, articleId, document, baseRevision),
      reload: () => getArticleDraft(getToken, articleId),
      onState: (state) => {
        setDirty(state.dirty);
        setSaveFailed(state.kind === "failed");
        if (state.kind === "saving") setSaveMessage("جارٍ الحفظ التلقائي…");
        else if (state.kind === "saved") setSaveMessage("تم الحفظ تلقائياً.");
        else if (state.kind === "failed") setSaveMessage(state.message);
        else if (state.kind === "conflict") {
          setSaveMessage(null);
          setConflictNotice(state.message);
        } else setSaveMessage(null);
      },
      onConflict: applyRevisionToEditor,
      onCanonical: applyRevisionToEditor,
    });
  }, [applyRevisionToEditor, articleId, getToken]);

  const imageAssetListCache = useMemo(
    () =>
      createButexImageAssetListCache(async () => {
        const { assets } = await listArticleAssets(getToken, articleId);
        return assets;
      }),
    [articleId, getToken],
  );

  const listButexImageAssets = useCallback(async (): Promise<
    ImageAssetRef[]
  > => {
    // يتغير المفتاح بعد تحديث الكاش كي تعيد كتل BuTeX قراءة المخزون.
    void assetListRevision;
    try {
      const assets = await imageAssetListCache.list();
      setAssetListError(null);
      return assets;
    } catch (err) {
      setAssetListError(userFacingErrorMessage(err, "تعذّر تحميل صور المقال."));
      throw err;
    }
  }, [assetListRevision, imageAssetListCache]);

  const handleAssetsListed = useCallback(
    (assets: Parameters<typeof imageAssetListCache.prime>[0]) => {
      imageAssetListCache.prime(assets);
      setAssetListError(null);
      setAssetListRevision((revision) => revision + 1);
    },
    [imageAssetListCache],
  );

  const handleRetryAssetList = useCallback(async () => {
    imageAssetListCache.invalidate();
    setAssetListRetrying(true);
    try {
      await imageAssetListCache.list();
      setAssetListError(null);
      setAssetListRevision((revision) => revision + 1);
    } catch (err) {
      setAssetListError(userFacingErrorMessage(err, "تعذّر تحميل صور المقال."));
    } finally {
      setAssetListRetrying(false);
    }
  }, [imageAssetListCache]);

  const resolvePendingImagePick = useCallback(
    (asset: ImageAssetRef | null) => {
      const resolve = pendingImagePickRef.current;
      pendingImagePickRef.current = null;
      resolve?.(asset);
    },
    [],
  );

  const restoreAssetsPanelFocus = useCallback(() => {
    const returnFocus = assetsPanelReturnFocusRef.current;
    assetsPanelReturnFocusRef.current = null;
    if (!returnFocus) return;
    requestAnimationFrame(() => {
      if (returnFocus.isConnected) returnFocus.focus();
    });
  }, []);

  const closeAssetsPanel = useCallback(() => {
    setAssetsPanelMode(null);
    setPickerCurrentAssetId(null);
    resolvePendingImagePick(null);
    restoreAssetsPanelFocus();
  }, [resolvePendingImagePick, restoreAssetsPanelFocus]);

  const handleImageAssetSelected = useCallback(
    (asset: ImageAssetRef) => {
      setAssetsPanelMode(null);
      setPickerCurrentAssetId(null);
      resolvePendingImagePick(asset);
      restoreAssetsPanelFocus();
    },
    [resolvePendingImagePick, restoreAssetsPanelFocus],
  );

  const handleRequestImagePick = useCallback(
    ({ current }: { blockId: string; current: ImageAssetRef | null }) => {
      pendingImagePickRef.current?.(null);
      assetsPanelReturnFocusRef.current =
        document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      setPickerCurrentAssetId(current?.assetId ?? null);
      setAssetsPanelMode("pick");
      return new Promise<ImageAssetRef | null>((resolve) => {
        pendingImagePickRef.current = resolve;
      });
    },
    [],
  );

  useEffect(() => {
    return () => {
      pendingImagePickRef.current?.(null);
      pendingImagePickRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        const data = await getArticle(getToken, articleId);
        if (cancelled) return;

        if (data.status !== "draft" && data.status !== "revision_requested") {
          // المخطوطة مجمّدة — لا محرر
          router.replace(`/maktabi/maqalati/${articleId}`);
          setPhase("blocked");
          return;
        }

        setArticle(data);

        const payload = await getArticleDraft(getToken, articleId);
        const doc = payload.document;
        if (cancelled) return;

        await ensureButexMathJax();
        if (cancelled) return;

        latestDocumentJson.current = doc;
        setDocumentValid(doc == null || isButexDocumentValid(doc));
        setInitialDocument(doc);
        if (isDevMode()) {
          setLiveDocument(doc);
        }
        if (doc) prefetchFromDocument(doc);
        installAutosaveController(payload);
        setPhase("ready");
      } catch (err) {
        if (!cancelled) {
          setError(userFacingErrorMessage(err, "تعذّر فتح المحرر."));
        }
      }
    }

    void boot();
    return () => {
      cancelled = true;
      autosaveController.current?.dispose();
      autosaveController.current = null;
    };
  }, [getToken, articleId, router, prefetchFromDocument, installAutosaveController]);

  useEffect(() => {
    const root = editorRootRef.current;
    const actionBar = actionBarRef.current;
    if (!root || !actionBar) return;

    const updateStickyOffset = () => {
      root.style.setProperty(
        "--article-editor-actions-height",
        `${actionBar.getBoundingClientRect().height}px`,
      );
    };

    updateStickyOffset();
    const observer = new ResizeObserver(updateStickyOffset);
    observer.observe(actionBar);
    window.addEventListener("resize", updateStickyOffset);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateStickyOffset);
    };
  }, []);

  useEffect(() => {
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (autosaveController.current?.isUnsafeToLeave()) {
        event.preventDefault();
        event.returnValue = "";
      }
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, []);

  useEffect(() => {
    function onLinkClick(event: MouseEvent) {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey ||
        !autosaveController.current?.isUnsafeToLeave()
      ) return;
      const target = event.target;
      const anchor = target instanceof Element ? target.closest("a[href]") : null;
      if (!(anchor instanceof HTMLAnchorElement) || anchor.target === "_blank" || anchor.download) {
        return;
      }
      const destination = new URL(anchor.href, window.location.href);
      if (
        destination.pathname === window.location.pathname &&
        destination.search === window.location.search &&
        destination.hash
      ) return;

      event.preventDefault();
      void (async () => {
        const saved = await autosaveController.current?.flush();
        const stillUnsafe = autosaveController.current?.isUnsafeToLeave() ?? false;
        if (
          saved === false &&
          stillUnsafe &&
          !window.confirm("تعذّر حفظ أحدث التغييرات. هل تريد المغادرة وفقدانها؟")
        ) return;
        if (destination.origin === window.location.origin) {
          router.push(`${destination.pathname}${destination.search}${destination.hash}`);
        } else {
          window.location.assign(destination.href);
        }
      })();
    }

    document.addEventListener("click", onLinkClick, true);
    return () => document.removeEventListener("click", onLinkClick, true);
  }, [router]);

  const handleDocumentJsonChange = useCallback(
    (doc: Document2Json) => {
      latestDocumentJson.current = doc;
      syncVisibleMetadata(doc);
      setDocumentValid(isButexDocumentValid(doc));
      autosaveController.current?.update(doc);

      prefetchFromDocument(doc);
      if (isDevMode()) setLiveDocument(doc);
    },
    [prefetchFromDocument, syncVisibleMetadata],
  );

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const saved = await autosaveController.current?.flush();
      if (saved === false) {
        setError("تعذّر حفظ أحدث التغييرات؛ لن يتم تقديم المقال حتى ينجح الحفظ.");
        setSubmitting(false);
        setDialogOpen(false);
        return;
      }
      await submitArticle(getToken, articleId);
      setDirty(false);
      router.push(`/maktabi/maqalati/${articleId}`);
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تقديم المقال."));
      setSubmitting(false);
      setDialogOpen(false);
    }
  }

  async function handleBack() {
    const saved = await autosaveController.current?.flush();
    if (
      saved === false &&
      !window.confirm("تعذّر حفظ أحدث التغييرات. هل تريد المغادرة وفقدانها؟")
    ) return;
    router.push(`/maktabi/maqalati/${articleId}`);
  }

  function handleOpenHistory() {
    setError(null);
    setHistoryOpen(true);
  }

  async function handleRestoreHistory(revision: DraftRevisionHistoryItem) {
    const controller = autosaveController.current;
    if (!controller) throw new ApiError("تعذّر تهيئة استعادة النسخة.", 409);
    const saved = await controller.flush();
    if (saved === false && controller.isUnsafeToLeave()) {
      throw new ApiError("تعذّر حفظ أحدث التغييرات؛ لن تبدأ الاستعادة.", 409);
    }
    try {
      const restored = await restoreDraftRevision(
        getToken,
        articleId,
        revision.revision_id,
        controller.getBaseRevision(),
      );
      applyRevisionToEditor(restored);
      installAutosaveController(restored);
      setArticle((current) => current ? {
        ...current,
        current_draft_revision_id: restored.revision_id,
        draft_revision_number: restored.revision_number,
      } : current);
      setHistoryOpen(false);
      setConflictNotice(
        `تمت استعادة النسخة ${formatDigits(String(revision.revision_number))} كنسخة حالية جديدة ${formatDigits(String(restored.revision_number))}. يبدأ التراجع والإعادة في جلسة التحرير من هذه الحالة من جديد، وتبقى الحالة التي كانت حالية قبل الاستعادة متاحة من سجل النسخ ما دامت ضمن النسخ المحفوظة.`,
      );
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const latest = await getArticleDraft(getToken, articleId);
        applyRevisionToEditor(latest);
        installAutosaveController(latest);
        setHistoryRefreshKey((key) => key + 1);
        setConflictNotice(
          "وصلت تعديلات أحدث من مصدر آخر؛ حُمّلت أحدث مسودة وأُلغيت الاستعادة.",
        );
        throw new ApiError("تغيّرت المسودة؛ حُدّث سجل النسخ وأُلغيت الاستعادة.", 409);
      }
      throw err;
    }
  }

  return (
    <div
      ref={editorRootRef}
      className="article-editor flex flex-1 flex-col bg-[var(--journal-paper)]"
    >
      <ArticleEditorHeader
        ref={actionBarRef}
        articleTitle={article?.title}
        ready={phase === "ready"}
        saveMessage={saveMessage}
        saveFailed={saveFailed}
        dirty={dirty}
        assetsUploading={assetsUploading}
        resubmission={article?.status === "revision_requested"}
        showDevJson={showDevJson}
        onBack={() => void handleBack()}
        onOpenAssets={(returnFocus) => {
          assetsPanelReturnFocusRef.current = returnFocus;
          setPickerCurrentAssetId(null);
          setAssetsPanelMode("manage");
        }}
        onOpenEquationMappings={() => setEquationMappingsOpen(true)}
        onOpenHistory={handleOpenHistory}
        onOpenJson={() => setJsonDialogOpen(true)}
        onSubmit={() => setDialogOpen(true)}
      />

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {conflictNotice ? (
          <div
            className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
            role="alert"
          >
            <p className="min-w-0 flex-1">{conflictNotice}</p>
            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setConflictNotice(null);
                  setHistoryOpen(true);
                }}
                className="rounded-md border border-amber-400 bg-white px-3 py-1 text-xs font-semibold"
              >
                عرض سجل النسخ
              </button>
              <button
                type="button"
                onClick={() => setConflictNotice(null)}
                className="rounded-md border border-amber-400 bg-white px-3 py-1 text-xs font-semibold"
              >
                حسناً
              </button>
            </div>
          </div>
        ) : null}

        {error ? (
          <p
            className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        {assetListError ? (
          <div
            className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            <p>
              تعذّر تحميل مخزون صور المقال. قد تكون الصور موجودة؛
              لكن تعذّر جلبها: {assetListError}
            </p>
            <button
              type="button"
              onClick={() => void handleRetryAssetList()}
              disabled={assetListRetrying}
              className="min-h-9 rounded-md border border-red-300 bg-white px-3 text-xs font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {assetListRetrying ? "جارٍ إعادة المحاولة…" : "إعادة المحاولة"}
            </button>
          </div>
        ) : null}

        {!documentValid ? (
          <p
            className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
            role="status"
          >
            توجد مشكلة في المحرر. راجع الحقول المعلّمة كي ينجح
            الحفظ التلقائي ويمكنك إنشاء ملفّ المعاينة.
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
            initialDocument={initialDocument}
            uiLocale="ar"
            documentDirection="rtl"
            equationSide="arabic"
            mathOutput="svg"
            editableEquations
            resolveImageUrl={resolveImageUrl}
            listImageAssets={listButexImageAssets}
            onRequestImagePick={handleRequestImagePick}
            onDocumentJsonChange={handleDocumentJsonChange}
          />
        ) : null}
      </main>

      <SubmitDialog
        open={dialogOpen}
        submitting={submitting}
        onConfirm={handleSubmit}
        onCancel={() => setDialogOpen(false)}
        resubmission={article?.status === "revision_requested"}
      />

      <EquationMappingsPanel
        open={equationMappingsOpen}
        articleId={articleId}
        getToken={getToken}
        onClose={() => setEquationMappingsOpen(false)}
      />

      <DraftHistoryDialog
        key={historyRefreshKey}
        open={historyOpen}
        articleId={articleId}
        getToken={getToken}
        onClose={() => setHistoryOpen(false)}
        onRestore={handleRestoreHistory}
        latestChangesUnsaved={dirty || saveFailed}
        currentDocument={
          dirty || saveFailed ? null : latestDocumentJson.current
        }
      />

      {showDevJson ? (
        <DocumentJsonDevDialog
          open={jsonDialogOpen}
          value={liveDocument}
          onClose={() => setJsonDialogOpen(false)}
        />
      ) : null}

      <ArticleAssetsPanel
        open={assetsPanelMode !== null}
        mode={assetsPanelMode ?? "manage"}
        articleId={articleId}
        getToken={getToken}
        resolveImageUrl={resolveImageUrl}
        ensureAsset={ensureAsset}
        currentAssetId={pickerCurrentAssetId}
        onSelectAsset={handleImageAssetSelected}
        onClose={closeAssetsPanel}
        onAssetsListed={handleAssetsListed}
        onUploadingChange={setAssetsUploading}
      />
    </div>
  );
}
