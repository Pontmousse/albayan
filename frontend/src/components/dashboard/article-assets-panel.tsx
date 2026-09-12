"use client";

import { Check, ImageOff, Link2, RefreshCw, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ImageAssetRef } from "@drghaliasri/butex/react-document2";
import { ArticleAssetDeleteDialog } from "@/components/dashboard/article-asset-delete-dialog";
import { useNumerals } from "@/components/numeral-provider";
import { useOpenTransition } from "@/hooks/use-open-transition";
import {
  deleteArticleAsset,
  listArticleAssets,
  uploadArticleAsset,
  type ArticleAssetSummary,
} from "@/lib/api/articles";
import {
  articleAssetDisplayLabel,
  articleAssetSize,
  articleAssetToButexImageAsset,
  articleAssetTypeLabel,
} from "@/lib/butex-image-assets";
import { getTrackedArticleAssetKeys } from "@/lib/butex-images";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;
type ResolveImageUrl = (ref: { assetId?: string; value: string }) => string;
export type ArticleAssetsPanelMode = "manage" | "pick";

const ASSETS_PANEL_EXIT_MS = 260;

type ArticleAssetsPanelProps = {
  open: boolean;
  mode: ArticleAssetsPanelMode;
  articleId: string;
  getToken: GetToken;
  resolveImageUrl: ResolveImageUrl;
  ensureAsset: (assetKey: string) => Promise<void>;
  currentAssetId?: string | null;
  onSelectAsset?: (asset: ImageAssetRef) => void;
  onClose: () => void;
  onAssetsListed?: (assets: ArticleAssetSummary[]) => void;
  onUploadingChange?: (uploading: boolean) => void;
};

type ThumbnailStatus = "idle" | "loading" | "ready" | "error";

function LazyArticleAssetThumbnail({
  asset,
  resolveImageUrl,
  ensureAsset,
}: {
  asset: ArticleAssetSummary;
  resolveImageUrl: ResolveImageUrl;
  ensureAsset: (assetKey: string) => Promise<void>;
}) {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [status, setStatus] = useState<ThumbnailStatus>("idle");
  const [attempt, setAttempt] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root || shouldLoad) return;
    if (!("IntersectionObserver" in window)) {
      setShouldLoad(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        setShouldLoad(true);
        observer.disconnect();
      },
      { rootMargin: "200px 0px", threshold: 0.01 },
    );
    observer.observe(root);
    return () => observer.disconnect();
  }, [shouldLoad]);

  useEffect(() => {
    if (!shouldLoad) return;
    let alive = true;
    setStatus("loading");
    ensureAsset(asset.asset_id)
      .then(() => {
        if (alive) setStatus("ready");
      })
      .catch(() => {
        if (alive) setStatus("error");
      });
    return () => {
      alive = false;
    };
  }, [asset.asset_id, attempt, ensureAsset, shouldLoad]);

  const label = articleAssetDisplayLabel(asset);
  const previewUrl =
    status === "ready"
      ? resolveImageUrl({
          assetId: asset.asset_id,
          value: asset.asset_id,
        })
      : "";

  return (
    <div
      ref={rootRef}
      className="relative flex aspect-[4/3] items-center justify-center overflow-hidden bg-slate-50"
    >
      {previewUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={previewUrl}
          alt={label}
          loading="lazy"
          decoding="async"
          className="h-full w-full object-contain"
          onError={() => setStatus("error")}
        />
      ) : status === "error" ? (
        <div className="relative z-20 flex flex-col items-center gap-2 px-2 text-center text-xs text-slate-500">
          <ImageOff aria-hidden className="h-6 w-6 text-slate-400" />
          <span>تعذّرت المعاينة</span>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setAttempt((value) => value + 1);
            }}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-md border border-[var(--journal-border)] bg-white px-3 font-semibold text-[var(--journal-accent-strong)] shadow-sm transition hover:border-[var(--journal-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30"
          >
            <RefreshCw aria-hidden className="h-3.5 w-3.5" />
            إعادة المحاولة
          </button>
        </div>
      ) : (
        <span className="px-2 text-center text-xs text-slate-400">
          {status === "loading" ? "جارٍ تحميل المعاينة…" : "معاينة الصورة"}
        </span>
      )}
    </div>
  );
}

export function ArticleAssetsPanel({
  open,
  mode,
  articleId,
  getToken,
  resolveImageUrl,
  ensureAsset,
  currentAssetId = null,
  onSelectAsset,
  onClose,
  onAssetsListed,
  onUploadingChange,
}: ArticleAssetsPanelProps) {
  const { formatNumber } = useNumerals();
  const { mounted, visible } = useOpenTransition(open, ASSETS_PANEL_EXIT_MS);
  const [displayMode, setDisplayMode] = useState<ArticleAssetsPanelMode>(mode);
  const [assets, setAssets] = useState<ArticleAssetSummary[]>([]);
  const [referencedAssetIds, setReferencedAssetIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingAssetId, setDeletingAssetId] = useState<string | null>(null);
  const [deleteCandidate, setDeleteCandidate] =
    useState<ArticleAssetSummary | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const syncTrackedReferences = useCallback(() => {
    const tracked = new Set(getTrackedArticleAssetKeys(articleId));
    setReferencedAssetIds(tracked);
    return tracked;
  }, [articleId]);

  const refreshAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    syncTrackedReferences();
    try {
      const { assets: listed } = await listArticleAssets(getToken, articleId);
      setAssets(listed);
      onAssetsListed?.(listed);
      syncTrackedReferences();
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل الصور."));
    } finally {
      setLoading(false);
    }
  }, [articleId, getToken, onAssetsListed, syncTrackedReferences]);

  useEffect(() => {
    if (!open) return;
    setDisplayMode(mode);
    syncTrackedReferences();
    void refreshAssets();
  }, [mode, open, refreshAssets, syncTrackedReferences]);

  useEffect(() => {
    if (!mounted) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mounted]);

  useEffect(() => {
    if (!visible) return;
    const focusFrame = requestAnimationFrame(() => closeButtonRef.current?.focus());
    return () => cancelAnimationFrame(focusFrame);
  }, [visible]);

  useEffect(() => {
    if (!visible) return;

    function onKeyDown(event: KeyboardEvent) {
      if (deleteCandidate) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = Array.from(
        panelRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      ).filter((element) => element.getClientRects().length > 0);
      if (focusable.length === 0) {
        event.preventDefault();
        panelRef.current?.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [deleteCandidate, onClose, visible]);

  async function handleUpload(file: File | undefined) {
    if (!file || displayMode !== "manage") return;
    setUploading(true);
    onUploadingChange?.(true);
    setError(null);
    try {
      const { asset_id } = await uploadArticleAsset(getToken, articleId, file);
      void ensureAsset(asset_id).catch(() => undefined);
      await refreshAssets();
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر رفع الصورة."));
    } finally {
      setUploading(false);
      onUploadingChange?.(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function requestDelete(asset: ArticleAssetSummary) {
    if (displayMode !== "manage" || deletingAssetId) return;
    const currentReferences = syncTrackedReferences();
    if (currentReferences.has(asset.asset_id)) {
      setError(
        "لا يمكن حذف صورة مستخدمة داخل المقال. أزلها أو استبدلها في المحرر أولاً.",
      );
      return;
    }
    setError(null);
    setDeleteCandidate(asset);
  }

  async function confirmDelete() {
    const asset = deleteCandidate;
    if (!asset || deletingAssetId) return;

    const currentReferences = syncTrackedReferences();
    if (currentReferences.has(asset.asset_id)) {
      setDeleteCandidate(null);
      setError(
        "لا يمكن حذف صورة مستخدمة داخل المقال. أزلها أو استبدلها في المحرر أولاً.",
      );
      return;
    }

    setDeletingAssetId(asset.asset_id);
    setError(null);
    try {
      await deleteArticleAsset(getToken, articleId, asset.asset_id);
      setDeleteCandidate(null);
      await refreshAssets();
    } catch (err) {
      setDeleteCandidate(null);
      setError(userFacingErrorMessage(err, "تعذّر حذف الصورة."));
    } finally {
      setDeletingAssetId(null);
    }
  }

  if (!mounted) return null;

  const picking = displayMode === "pick";
  const durationMs = visible ? 340 : ASSETS_PANEL_EXIT_MS;

  return (
    <div
      className={`fixed inset-0 z-[60] flex justify-end bg-slate-950/40 backdrop-blur-[2px] transition-opacity motion-reduce:transition-none ${
        visible ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
      style={{
        transitionDuration: `${durationMs}ms`,
        transitionTimingFunction: visible
          ? "var(--motion-ease-out)"
          : "var(--motion-ease-in)",
      }}
      role="presentation"
      onClick={onClose}
    >
      <aside
        ref={panelRef}
        tabIndex={-1}
        className={`flex h-full w-full transform-gpu flex-col border-s border-[var(--journal-border)] bg-[var(--journal-paper)] shadow-2xl outline-none transition-[transform,opacity] motion-reduce:translate-x-0 motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none sm:max-w-xl ${
          visible
            ? "translate-y-0 opacity-100 sm:translate-x-0"
            : "translate-y-5 opacity-0 sm:translate-x-8 sm:translate-y-0"
        }`}
        style={{
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: visible
            ? "var(--motion-ease-out)"
            : "var(--motion-ease-in)",
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="article-assets-panel-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--journal-border)] px-4 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] sm:px-5">
          <div className="min-w-0">
            <h2
              id="article-assets-panel-title"
              className="text-base font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              {picking ? "اختيار صورة" : "صور المقال"}
            </h2>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {picking
                ? "اختر صورة من مخزون المقال لإضافتها إلى هذه الكتلة."
                : "ارفع صور المقال وراجعها هنا، ثم اخترها من كتلة الصورة في المحرر."}
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="inline-flex min-h-11 shrink-0 items-center rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30"
          >
            إغلاق
          </button>
        </header>

        <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-[var(--journal-border)] bg-white/55 px-4 py-3 sm:px-5">
          {!picking ? (
            <>
              <p className="w-full text-xs text-slate-500">
                JPEG، PNG، GIF أو WebP — بحد أقصى 5 ميغابايت.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                tabIndex={-1}
                accept="image/jpeg,image/png,image/gif,image/webp"
                className="sr-only"
                onChange={(event) => void handleUpload(event.target.files?.[0])}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || deletingAssetId !== null}
                className="min-h-11 rounded-md bg-[var(--journal-accent)] px-4 text-xs font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {uploading ? "جارٍ الرفع…" : "رفع صورة"}
              </button>
            </>
          ) : null}
          <button
            type="button"
            onClick={() => void refreshAssets()}
            disabled={loading || deletingAssetId !== null}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 disabled:opacity-60"
          >
            <RefreshCw
              aria-hidden
              className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
            />
            تحديث
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:px-5">
          {error ? (
            <div
              className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
              role="alert"
            >
              <p className="leading-6">{error}</p>
              <button
                type="button"
                onClick={() => void refreshAssets()}
                className="min-h-11 rounded-md border border-red-300 bg-white px-3 text-xs font-semibold text-red-700 transition hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300"
              >
                تحديث القائمة
              </button>
            </div>
          ) : null}

          {loading && assets.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500" role="status">
              جارٍ التحميل…
            </p>
          ) : null}

          {!loading && !error && assets.length === 0 ? (
            <p className="rounded-lg border border-dashed border-[var(--journal-border)] bg-white px-4 py-10 text-center text-sm leading-6 text-slate-500">
              {picking
                ? "لا توجد صور في مخزون المقال. يمكنك رفع الصور من زر «صور المقال» أعلى المحرر."
                : "لا توجد صور بعد. ارفع صورة لتظهر في مخزون المقال."}
            </p>
          ) : null}

          <ul className="grid grid-cols-2 gap-3" aria-busy={loading}>
            {assets.map((asset) => {
              const displayLabel = articleAssetDisplayLabel(asset);
              const typeLabel = articleAssetTypeLabel(asset);
              const size = articleAssetSize(asset.size);
              const selected = picking && currentAssetId === asset.asset_id;
              const deleting = deletingAssetId === asset.asset_id;
              const referenced = referencedAssetIds.has(asset.asset_id);
              const accessibleSize = size
                ? `${formatNumber(size.value, { maximumFractionDigits: 1 })} ${size.unit}`
                : "الحجم غير متاح";
              return (
                <li
                  key={asset.asset_id}
                  className={`group relative overflow-hidden rounded-xl border bg-white shadow-sm transition ${
                    selected
                      ? "border-[var(--journal-accent)] ring-2 ring-[var(--journal-accent)]/20"
                      : referenced && !picking
                        ? "border-amber-200"
                        : "border-[var(--journal-border)] hover:border-[var(--journal-accent)] hover:shadow-md"
                  }`}
                >
                  <LazyArticleAssetThumbnail
                    asset={asset}
                    resolveImageUrl={resolveImageUrl}
                    ensureAsset={ensureAsset}
                  />
                  <div className="space-y-2 p-3">
                    <p
                      className="truncate text-xs font-semibold text-slate-700"
                      dir="auto"
                      title={asset.asset_id}
                    >
                      {displayLabel}
                    </p>
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-600">
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 font-semibold">
                        {typeLabel}
                      </span>
                      <span className="rounded-full bg-slate-100 px-2 py-0.5">
                        {accessibleSize}
                      </span>
                    </div>
                    <p
                      className="truncate text-[10px] text-slate-500"
                      dir="ltr"
                      title={asset.asset_id}
                    >
                      {asset.asset_id}
                    </p>
                    {!picking ? (
                      referenced ? (
                        <div className="flex min-h-12 items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
                          <Link2 aria-hidden className="h-4 w-4 shrink-0" />
                          <div className="min-w-0">
                            <p className="text-[11px] font-bold">مستخدمة في المقال</p>
                            <p className="mt-0.5 text-[10px] leading-4 text-amber-800">
                              أزلها أو استبدلها في المستند أولاً.
                            </p>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => requestDelete(asset)}
                          disabled={deletingAssetId !== null || uploading}
                          className="inline-flex min-h-10 w-full items-center justify-center gap-1.5 rounded-md border border-red-200 bg-white px-3 text-xs font-semibold text-red-700 transition hover:border-red-300 hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-200 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <Trash2 aria-hidden className="h-3.5 w-3.5" />
                          {deleting ? "جارٍ الحذف…" : "حذف الصورة"}
                        </button>
                      )
                    ) : null}
                  </div>
                  {selected ? (
                    <span className="pointer-events-none absolute start-2 top-2 z-20 inline-flex items-center gap-1 rounded-full bg-[var(--journal-accent)] px-2 py-1 text-[10px] font-semibold text-white shadow-sm">
                      <Check aria-hidden className="h-3.5 w-3.5" />
                      الصورة الحالية
                    </span>
                  ) : null}
                  {picking ? (
                    <button
                      type="button"
                      aria-label={`اختيار ${displayLabel}، ${typeLabel}، ${accessibleSize}`}
                      aria-current={selected ? "true" : undefined}
                      title={displayLabel}
                      onClick={() =>
                        onSelectAsset?.(articleAssetToButexImageAsset(asset))
                      }
                      className="absolute inset-0 z-10 rounded-xl focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--journal-accent)]/35"
                    >
                      <span className="sr-only">اختيار الصورة</span>
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      </aside>

      <ArticleAssetDeleteDialog
        open={deleteCandidate !== null}
        assetLabel={
          deleteCandidate ? articleAssetDisplayLabel(deleteCandidate) : "الصورة"
        }
        deleting={deletingAssetId !== null}
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          if (!deletingAssetId) setDeleteCandidate(null);
        }}
      />
    </div>
  );
}
