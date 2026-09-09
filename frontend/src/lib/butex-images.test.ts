import { describe, expect, it, vi } from "vitest";
import type { ArticleAssetSummary } from "./api/articles";
import {
  articleAssetDisplayLabel,
  articleAssetSize,
  articleAssetTypeLabel,
  articleAssetsToButexImageAssets,
  createButexImageAssetListCache,
} from "./butex-image-assets";

function asset(
  assetId: string,
  overrides: Partial<ArticleAssetSummary> = {},
): ArticleAssetSummary {
  return {
    asset_id: assetId,
    content_type: "image/png",
    size: 128,
    updated_at: null,
    ...overrides,
  };
}

describe("articleAssetsToButexImageAssets", () => {
  it("uses the article asset id as both BuTeX identity and value", () => {
    expect(articleAssetsToButexImageAssets([asset("assets/figure.png")])).toEqual(
      [
        {
          assetId: "assets/figure.png",
          value: "assets/figure.png",
          label: "figure.png",
        },
      ],
    );
  });

  it("keeps canonical ids while making generated names easier to scan", () => {
    const generated = asset(
      "assets/0123456789abcdef0123456789abcdef.png",
    );

    expect(articleAssetsToButexImageAssets([generated])).toEqual([
      {
        assetId: generated.asset_id,
        value: generated.asset_id,
        label: "PNG — 01234567…",
      },
    ]);
    expect(articleAssetDisplayLabel(asset("assets/field-notes.webp"))).toBe(
      "field-notes.webp",
    );
  });

  it("derives image type labels from MIME or extension", () => {
    expect(
      articleAssetTypeLabel(
        asset("assets/photo.bin", { content_type: "image/jpeg" }),
      ),
    ).toBe("JPEG");
    expect(
      articleAssetTypeLabel(
        asset("assets/animation.gif", { content_type: null }),
      ),
    ).toBe("GIF");
    expect(
      articleAssetTypeLabel(asset("assets/unknown.bin", { content_type: null })),
    ).toBe("صورة");
  });

  it("reports useful binary size units and missing sizes", () => {
    expect(articleAssetSize(0)).toBeNull();
    expect(articleAssetSize(512)).toEqual({ value: 512, unit: "بايت" });
    expect(articleAssetSize(1536)).toEqual({
      value: 1.5,
      unit: "كيلوبايت",
    });
    expect(articleAssetSize(5 * 1024 * 1024)).toEqual({
      value: 5,
      unit: "ميغابايت",
    });
  });
});

describe("createButexImageAssetListCache", () => {
  it("coalesces concurrent calls and reuses a successful result", async () => {
    let resolveLoad!: (assets: ArticleAssetSummary[]) => void;
    const load = vi.fn(
      () =>
        new Promise<ArticleAssetSummary[]>((resolve) => {
          resolveLoad = resolve;
        }),
    );
    const cache = createButexImageAssetListCache(load);

    const first = cache.list();
    const second = cache.list();
    expect(first).toBe(second);
    expect(load).toHaveBeenCalledTimes(1);

    resolveLoad([asset("assets/one.png")]);
    await expect(first).resolves.toEqual([
      {
        assetId: "assets/one.png",
        value: "assets/one.png",
        label: "one.png",
      },
    ]);
    await cache.list();
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("does not cache a failed request and allows retry", async () => {
    const load = vi
      .fn<() => Promise<ArticleAssetSummary[]>>()
      .mockRejectedValueOnce(new Error("network unavailable"))
      .mockResolvedValueOnce([asset("assets/retry.png")]);
    const cache = createButexImageAssetListCache(load);

    await expect(cache.list()).rejects.toThrow("network unavailable");
    await expect(cache.list()).resolves.toEqual([
      {
        assetId: "assets/retry.png",
        value: "assets/retry.png",
        label: "retry.png",
      },
    ]);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("can be primed from the panel and invalidated explicitly", async () => {
    const load = vi.fn(async () => [asset("assets/from-api.png")]);
    const cache = createButexImageAssetListCache(load);

    cache.prime([asset("assets/from-panel.png")]);
    await expect(cache.list()).resolves.toEqual([
      {
        assetId: "assets/from-panel.png",
        value: "assets/from-panel.png",
        label: "from-panel.png",
      },
    ]);
    expect(load).not.toHaveBeenCalled();

    cache.invalidate();
    await expect(cache.list()).resolves.toEqual([
      {
        assetId: "assets/from-api.png",
        value: "assets/from-api.png",
        label: "from-api.png",
      },
    ]);
    expect(load).toHaveBeenCalledTimes(1);
  });
});
