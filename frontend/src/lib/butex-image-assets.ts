import type { ImageAssetRef } from "@drghaliasri/butex/react-document2";
import type { ArticleAssetSummary } from "./api/articles";

const IMAGE_TYPE_LABELS: Record<string, string> = {
  "image/jpeg": "JPEG",
  "image/png": "PNG",
  "image/gif": "GIF",
  "image/webp": "WebP",
};

function assetFileName(assetId: string): string {
  return assetId.replace(/^assets\//, "");
}

export function articleAssetTypeLabel(asset: ArticleAssetSummary): string {
  const fromMime = asset.content_type
    ? IMAGE_TYPE_LABELS[asset.content_type.toLowerCase()]
    : undefined;
  if (fromMime) return fromMime;

  const extension = assetFileName(asset.asset_id).split(".").pop()?.toLowerCase();
  return extension === "jpg" || extension === "jpeg"
    ? "JPEG"
    : extension === "png"
      ? "PNG"
      : extension === "gif"
        ? "GIF"
        : extension === "webp"
          ? "WebP"
          : "صورة";
}

export function articleAssetDisplayLabel(asset: ArticleAssetSummary): string {
  const fileName = assetFileName(asset.asset_id);
  const generatedName = /^([0-9a-f]{32})\.(?:jpe?g|png|gif|webp)$/i.exec(
    fileName,
  );
  if (!generatedName) return fileName;
  return `${articleAssetTypeLabel(asset)} — ${generatedName[1].slice(0, 8)}…`;
}

export type ArticleAssetSize = {
  value: number;
  unit: "بايت" | "كيلوبايت" | "ميغابايت";
};

export function articleAssetSize(size: number): ArticleAssetSize | null {
  if (!Number.isFinite(size) || size <= 0) return null;
  if (size >= 1024 * 1024) {
    return { value: size / (1024 * 1024), unit: "ميغابايت" };
  }
  if (size >= 1024) return { value: size / 1024, unit: "كيلوبايت" };
  return { value: size, unit: "بايت" };
}

export function articleAssetsToButexImageAssets(
  assets: ArticleAssetSummary[],
): ImageAssetRef[] {
  return assets.map((asset) => ({
    assetId: asset.asset_id,
    value: asset.asset_id,
    label: articleAssetDisplayLabel(asset),
  }));
}

export type ButexImageAssetListCache = {
  list: () => Promise<ImageAssetRef[]>;
  prime: (assets: ArticleAssetSummary[]) => ImageAssetRef[];
  invalidate: () => void;
};

/** يشارك طلب مخزون الصور ونتيجته بين كتل BuTeX المفتوحة. */
export function createButexImageAssetListCache(
  loadAssets: () => Promise<ArticleAssetSummary[]>,
): ButexImageAssetListCache {
  let cached: ImageAssetRef[] | null = null;
  let inflight: Promise<ImageAssetRef[]> | null = null;
  let generation = 0;

  return {
    list() {
      if (cached !== null) return Promise.resolve(cached);
      if (inflight) return inflight;

      const requestGeneration = generation;
      const request: Promise<ImageAssetRef[]> = loadAssets()
        .then(articleAssetsToButexImageAssets)
        .then((assets) => {
          if (requestGeneration === generation) cached = assets;
          return assets;
        })
        .finally(() => {
          if (inflight === request) inflight = null;
        });
      inflight = request;
      return request;
    },
    prime(assets) {
      generation += 1;
      cached = articleAssetsToButexImageAssets(assets);
      inflight = null;
      return cached;
    },
    invalidate() {
      generation += 1;
      cached = null;
      inflight = null;
    },
  };
}
