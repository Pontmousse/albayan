"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import type { Document2Json, Document2Node } from "@drghaliasri/butex/document2";
import { SkeletonBlock } from "@/components/dashboard/skeleton";
import {
  useButexImageResolver,
  type FetchAssetBlob,
} from "@/lib/butex-images";
import { ensureButexMathJax } from "@/lib/butex-mathjax";
import { ALBAYAN_BUTEX_THEME_CLASS } from "@/lib/butex-theme";

const ButexDocumentEditor2 = dynamic(
  () =>
    import("@drghaliasri/butex/react-document2").then(
      (mod) => mod.ButexDocumentEditor2,
    ),
  { ssr: false },
);

type GetToken = () => Promise<string | null>;

/** معاينة مجمّدة — ButexDocumentEditor2 مع previewOnly (BuTeX 4.3+). */
export function DocumentFrozenPreview({
  documentJson,
  articleId,
  getToken,
  fetchAssetBlob,
}: {
  documentJson: unknown;
  articleId: string;
  getToken: GetToken;
  fetchAssetBlob?: FetchAssetBlob;
}) {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { resolveImageUrl, prefetchFromDocument } = useButexImageResolver(
    articleId,
    getToken,
    fetchAssetBlob,
  );

  useEffect(() => {
    let cancelled = false;
    ensureButexMathJax()
      .then(() => {
        if (!cancelled) setReady(true);
      })
      .catch(() => {
        if (!cancelled) setError("تعذّر تهيئة عرض المعادلات.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (documentJson != null) {
      prefetchFromDocument(documentJson);
    }
  }, [documentJson, prefetchFromDocument]);

  if (documentJson == null) {
    return (
      <p className="rounded-md border border-dashed border-amber-300 bg-white/60 px-4 py-6 text-center text-sm text-slate-500">
        لا محتوى بعد — المخطوطة فارغة.
      </p>
    );
  }

  if (error) {
    return (
      <p
        className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
        role="alert"
      >
        {error}
      </p>
    );
  }

  if (!ready) {
    return (
      <div className="space-y-3">
        <SkeletonBlock className="h-6 w-2/3" />
        <SkeletonBlock className="h-4" />
        <SkeletonBlock className="h-4 w-5/6" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-white p-5">
      <ButexDocumentEditor2
        className={ALBAYAN_BUTEX_THEME_CLASS}
        initialDocument={documentJson as Document2Json | Document2Node}
        previewOnly
        documentDirection="rtl"
        uiLocale="ar"
        mathOutput="svg"
        resolveImageUrl={resolveImageUrl}
      />
    </div>
  );
}
