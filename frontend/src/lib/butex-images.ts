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

const trackedAssetKeysByScope = new Map<string, string[]>();

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

/** يجمع مفاتيح الصور المستخدمة في أي موضع داخل JSON الحالي للمحرر. */
export function collectAssetKeysFromDocument(documentJson: unknown): string[] {
  const keys = new Set<string>();

  function visit(value: unknown) {
    if (Array.isArray(value)) {
      for (const item of value) visit(item);
      return;
    }
    if (!value || typeof value !== "object") return;

    const node = value as Record<string, unknown>;
    if (node.kind === "image" || node.command === "\\includegraphics") {
      for (const candidate of [
        node.assetId,
        node.asset_id,
        node.value,
        node.src,
      ]) {
        if (typeof candidate !== "string") continue;
        const key = normalizeAssetKey(candidate);
        if (key) keys.add(key);
      }
    }

    for (const child of Object.values(node)) {
      if (child && typeof child === "object") visit(child);
    }
  }

  visit(documentJson);
  return [...keys].sort();
}

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
