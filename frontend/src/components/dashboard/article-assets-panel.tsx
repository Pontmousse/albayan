"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useNumerals } from "@/components/numeral-provider";
import {
  listArticleAssets,
  uploadArticleAsset,
  type ArticleAssetSummary,
} from "@/lib/api/articles";
import {
  articleAssetDisplayLabel,
  articleAssetSize,
  articleAssetTypeLabel,
} from "@/lib/butex-image-assets";

type GetToken = () => Promise<string | null>;
type ResolveImageUrl = (ref: { assetId?: string; value: string }) => string;

type ArticleAssetsPanelProps = {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  resolveImageUrl: ResolveImageUrl;
  ensureAsset: (assetKey: string) => Promise<void>;
  onClose: () => void;
  onAssetsListed?: (assets: ArticleAssetSummary[]) => void;
  onUploadingChange?: (uploading: boolean) => void;
};

function LazyArticleAssetThumbnail({
  asset,
  resolveImageUrl,
}: {
  asset: ArticleAssetSummary;
  resolveImageUrl: ResolveImageUrl;
}) {
  const [shouldLoad, setShouldLoad] = useState(false);
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

  const label = articleAssetDisplayLabel(asset);
  const previewUrl = shouldLoad
    ? resolveImageUrl({
        assetId: asset.asset_id,
        value: asset.asset_id,
      })
    : "";

  return (
    <div
      ref={rootRef}
      className="flex aspect-[4/3] items-center justify-center overflow-hidden bg-slate-50"
    >
      {previewUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={previewUrl}
          alt={label}
          loading="lazy"
          decoding="async"
          className="h-full w-full object-contain"
        />
      ) : (
        <span className="text-xs text-slate-400">
          {shouldLoad ? "جارٍ تحميل المعاينة…" : "معاينة الصورة"}
        </span>
      )}
    </div>
  );
}

export function ArticleAssetsPanel({
  open,
  articleId,
  getToken,
  resolveImageUrl,
  ensureAsset,
  onClose,
  onAssetsListed,
  onUploadingChange,
}: ArticleAssetsPanelProps) {
  const { formatNumber } = useNumerals();
  const [assets, setAssets] = useState<ArticleAssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { assets: listed } = await listArticleAssets(getToken, articleId);
      setAssets(listed);
      onAssetsListed?.(listed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل الصور.");
    } finally {
      setLoading(false);
    }
  }, [articleId, getToken, onAssetsListed]);

  useEffect(() => {
    if (!open) return;
    void refreshAssets();
  }, [open, refreshAssets]);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  async function handleUpload(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    onUploadingChange?.(true);
    setError(null);
    try {
      const { asset_id } = await uploadArticleAsset(getToken, articleId, file);
      await ensureAsset(asset_id);
      await refreshAssets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر رفع الصورة.");
    } finally {
      setUploading(false);
      onUploadingChange?.(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-black/35"
      role="presentation"
      onClick={onClose}
    >
      <aside
        className="flex h-full w-full max-w-md flex-col border-s border-[var(--journal-border)] bg-[var(--journal-paper)] shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="article-assets-panel-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-3 border-b border-[var(--journal-border)] px-4 py-3">
          <div>
            <h2
              id="article-assets-panel-title"
              className="text-sm font-bold text-slate-900"
            >
              صور المقال
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              ارفع صور المقال وراجعها هنا، ثم اخترها من كتلة الصورة في المحرر.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-600"
          >
            إغلاق
          </button>
        </header>

        <div className="flex flex-wrap items-center gap-2 border-b border-[var(--journal-border)] px-4 py-3">
          <p className="w-full text-xs text-slate-500">
            JPEG، PNG، GIF أو WebP — بحد أقصى 5 ميغابايت.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            className="sr-only"
            onChange={(event) => void handleUpload(event.target.files?.[0])}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="min-h-9 rounded-md bg-[var(--journal-accent)] px-4 text-xs font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? "جارٍ الرفع…" : "رفع صورة"}
          </button>
          <button
            type="button"
            onClick={() => void refreshAssets()}
            disabled={loading}
            className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-700 disabled:opacity-60"
          >
            تحديث
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {error ? (
            <p
              className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          {loading && assets.length === 0 ? (
            <p className="text-center text-sm text-slate-500">جارٍ التحميل…</p>
          ) : null}

          {!loading && !error && assets.length === 0 ? (
            <p className="rounded-md border border-dashed border-[var(--journal-border)] bg-white px-4 py-8 text-center text-sm text-slate-500">
              لا توجد صور بعد. ارفع صورة لتظهر في مخزون المقال.
            </p>
          ) : null}

          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-2">
            {assets.map((asset) => {
              const displayLabel = articleAssetDisplayLabel(asset);
              const typeLabel = articleAssetTypeLabel(asset);
              const size = articleAssetSize(asset.size);
              return (
                <li
                  key={asset.asset_id}
                  className="overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white"
                >
                  <LazyArticleAssetThumbnail
                    asset={asset}
                    resolveImageUrl={resolveImageUrl}
                  />
                  <div className="space-y-2 p-2.5">
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
                        {size
                          ? `${formatNumber(size.value, { maximumFractionDigits: 1 })} ${size.unit}`
                          : "الحجم غير متاح"}
                      </span>
                    </div>
                    <p
                      className="truncate text-[10px] text-slate-500"
                      dir="ltr"
                      title={asset.asset_id}
                    >
                      {asset.asset_id}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>
    </div>
  );
}
