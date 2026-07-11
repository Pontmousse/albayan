"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchArticleAssetBlob } from "@/lib/api/articles";

type GetToken = () => Promise<string | null>;

export type FetchAssetBlob = (
  getToken: GetToken,
  scopeId: string,
  assetKey: string,
) => Promise<Blob>;

type ImageRef = {
  assetId?: string;
  value: string;
};

/** يحوّل قيمة مسار إلى مفتاح أصل نسبي مثل assets/uuid.jpg */
export function normalizeAssetKey(raw: string | undefined | null): string | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  if (/^https?:\/\//i.test(trimmed) || trimmed.startsWith("blob:")) {
    return null;
  }
  if (trimmed.startsWith("assets/")) {
    const name = trimmed.slice("assets/".length);
    if (!name || name.includes("/") || name.includes("..")) return null;
    return `assets/${name}`;
  }
  return null;
}

function collectAssetKeysFromDocument(documentJson: unknown): string[] {
  const keys = new Set<string>();

  function visitBlocks(blocks: unknown) {
    if (!Array.isArray(blocks)) return;
    for (const block of blocks) {
      if (!block || typeof block !== "object") continue;
      const b = block as Record<string, unknown>;
      if (b.kind === "image" || b.command === "\\includegraphics") {
        const fromId = normalizeAssetKey(
          typeof b.assetId === "string"
            ? b.assetId
            : typeof b.asset_id === "string"
              ? b.asset_id
              : null,
        );
        const fromValue = normalizeAssetKey(
          typeof b.value === "string"
            ? b.value
            : typeof b.src === "string"
              ? b.src
              : null,
        );
        if (fromId) keys.add(fromId);
        if (fromValue) keys.add(fromValue);
      }
      if (b.kind === "list" && Array.isArray(b.items)) {
        for (const item of b.items) {
          if (item && typeof item === "object") {
            visitBlocks((item as { blocks?: unknown }).blocks);
          }
        }
      }
    }
  }

  if (documentJson && typeof documentJson === "object") {
    visitBlocks((documentJson as { blocks?: unknown }).blocks);
  }
  return [...keys];
}

/**
 * يخزّن blob: URLs لأصول المقال ويوفّر resolveImageUrl المتزامن لـ BuTeX.
 */
export function useButexImageResolver(
  scopeId: string | undefined,
  getToken: GetToken,
  fetchAssetBlob: FetchAssetBlob = fetchArticleAssetBlob,
) {
  const [urlMap, setUrlMap] = useState<Record<string, string>>({});
  const urlMapRef = useRef(urlMap);
  urlMapRef.current = urlMap;
  const inflightRef = useRef(new Set<string>());
  const getTokenRef = useRef(getToken);
  getTokenRef.current = getToken;
  const fetchRef = useRef(fetchAssetBlob);
  fetchRef.current = fetchAssetBlob;

  useEffect(() => {
    return () => {
      for (const url of Object.values(urlMapRef.current)) {
        URL.revokeObjectURL(url);
      }
    };
  }, []);

  const ensureAsset = useCallback(
    async (assetKey: string) => {
      if (!scopeId) return;
      if (urlMapRef.current[assetKey] || inflightRef.current.has(assetKey)) {
        return;
      }
      inflightRef.current.add(assetKey);
      try {
        const blob = await fetchRef.current(
          getTokenRef.current,
          scopeId,
          assetKey,
        );
        const objectUrl = URL.createObjectURL(blob);
        setUrlMap((prev) => {
          if (prev[assetKey]) {
            URL.revokeObjectURL(objectUrl);
            return prev;
          }
          return { ...prev, [assetKey]: objectUrl };
        });
      } catch {
        // تُترك الصورة فارغة حتى إعادة المحاولة
      } finally {
        inflightRef.current.delete(assetKey);
      }
    },
    [scopeId],
  );

  const prefetchFromDocument = useCallback(
    (documentJson: unknown) => {
      for (const key of collectAssetKeysFromDocument(documentJson)) {
        void ensureAsset(key);
      }
    },
    [ensureAsset],
  );

  const resolveImageUrl = useCallback(
    ({ assetId, value }: ImageRef): string => {
      const key =
        normalizeAssetKey(assetId) ?? normalizeAssetKey(value) ?? null;
      if (key) {
        const cached = urlMap[key];
        if (cached) return cached;
        void ensureAsset(key);
        return "";
      }
      if (/^https?:\/\//i.test(value) || value.startsWith("blob:")) {
        return value;
      }
      return value;
    },
    [ensureAsset, urlMap],
  );

  return {
    resolveImageUrl,
    prefetchFromDocument,
    ensureAsset,
  };
}
