"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchArticleAssetBlob } from "@/lib/api/articles";
import {
  collectAssetKeysFromDocument,
  normalizeAssetKey,
} from "./butex-image-references";

export { collectAssetKeysFromDocument, normalizeAssetKey } from "./butex-image-references";

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

const trackedAssetKeysByScope = new Map<string, string[]>();

/** آخر مفاتيح صور رآها محرر المقال في الذاكرة، بما فيها التعديلات غير المحفوظة بعد. */
export function getTrackedArticleAssetKeys(scopeId: string): string[] {
  return [...(trackedAssetKeysByScope.get(scopeId) ?? [])];
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
  const inflightRef = useRef(new Map<string, Promise<void>>());
  const getTokenRef = useRef(getToken);
  getTokenRef.current = getToken;
  const fetchRef = useRef(fetchAssetBlob);
  fetchRef.current = fetchAssetBlob;

  useEffect(() => {
    return () => {
      for (const url of Object.values(urlMapRef.current)) {
        URL.revokeObjectURL(url);
      }
      if (scopeId) trackedAssetKeysByScope.delete(scopeId);
    };
  }, [scopeId]);

  const ensureAsset = useCallback(
    (assetKey: string): Promise<void> => {
      if (!scopeId || urlMapRef.current[assetKey]) return Promise.resolve();
      const inflight = inflightRef.current.get(assetKey);
      if (inflight) return inflight;

      const request = (async () => {
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
      })().finally(() => {
        if (inflightRef.current.get(assetKey) === request) {
          inflightRef.current.delete(assetKey);
        }
      });
      inflightRef.current.set(assetKey, request);
      return request;
    },
    [scopeId],
  );

  const prefetchFromDocument = useCallback(
    (documentJson: unknown) => {
      const keys = collectAssetKeysFromDocument(documentJson);
      if (scopeId) trackedAssetKeysByScope.set(scopeId, keys);
      for (const key of keys) {
        void ensureAsset(key).catch(() => undefined);
      }
    },
    [ensureAsset, scopeId],
  );

  const resolveImageUrl = useCallback(
    ({ assetId, value }: ImageRef): string => {
      const key =
        normalizeAssetKey(assetId) ?? normalizeAssetKey(value) ?? null;
      if (key) {
        const cached = urlMap[key];
        if (cached) return cached;
        void ensureAsset(key).catch(() => undefined);
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
