"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { VersionRead } from "@/lib/api/articles";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

export type CompileStatus = VersionRead["compile_status"];

type GetToken = () => Promise<string | null>;

export type CompiledPdfViewerProps = {
  compileStatus: CompileStatus;
  getToken: GetToken;
  fetchPdfBlob: (getToken: GetToken, scopeId: string) => Promise<Blob>;
  scopeId: string;
  /** عند التوفر يُظهر زر إنشاء/إعادة تجميع (المؤلف). */
  onRequestCompile?: () => Promise<void>;
  /** يُستدعى أثناء processing لإعادة جلب حالة التجميع. */
  onRefreshStatus?: () => Promise<void>;
};

const STATUS_COPY: Record<CompileStatus, string> = {
  pending: "لم يُنشأ ملفّ المعاينة بعد.",
  processing: "جارٍ إنشاء ملفّ المعاينة… قد يستغرق ذلك دقيقة أو أكثر.",
  success: "",
  failed: "تعذّر إنشاء ملفّ المعاينة. يمكنك إعادة المحاولة بعد مراجعة المخطوطة.",
};

function PdfPages({ fileUrl }: { fileUrl: string }) {
  const [numPages, setNumPages] = useState(0);
  const [page, setPage] = useState(1);
  const [width, setWidth] = useState(640);
  const containerRef = useRef<HTMLDivElement>(null);
  const [mods, setMods] = useState<{
    Document: typeof import("react-pdf").Document;
    Page: typeof import("react-pdf").Page;
  } | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const sync = () =>
      setWidth(Math.max(280, Math.min(el.clientWidth - 8, 900)));
    sync();
    const observer = new ResizeObserver(sync);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const reactPdf = await import("react-pdf");
      const { pdfjs, Document, Page } = reactPdf;
      pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
      if (!cancelled) setMods({ Document, Page });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!mods) {
    return (
      <p className="px-4 py-8 text-center text-sm text-slate-500">
        جارٍ تحميل عارض ملفّ المعاينة…
      </p>
    );
  }

  const { Document, Page } = mods;

  return (
    <div ref={containerRef} className="w-full">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-[var(--journal-border)] px-3 py-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-700 disabled:opacity-40"
          >
            السابق
          </button>
          <span className="text-xs text-slate-600">
            صفحة {page}
            {numPages ? ` من ${numPages}` : ""}
          </span>
          <button
            type="button"
            disabled={!numPages || page >= numPages}
            onClick={() => setPage((p) => Math.min(numPages, p + 1))}
            className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-700 disabled:opacity-40"
          >
            التالي
          </button>
        </div>
        <a
          href={fileUrl}
          download="compiled.pdf"
          className="text-xs font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          تنزيل ملفّ المعاينة
        </a>
      </div>
      <div className="overflow-x-auto px-2 pb-4">
        <Document
          file={fileUrl}
          loading={
            <p className="px-4 py-8 text-center text-sm text-slate-500">
              جارٍ فتح الملف…
            </p>
          }
          error={
            <p className="px-4 py-8 text-center text-sm text-red-700">
              تعذّر عرض ملفّ المعاينة.
            </p>
          }
          onLoadSuccess={({ numPages: n }) => {
            setNumPages(n);
            setPage(1);
          }}
        >
          <Page
            pageNumber={page}
            width={width}
            renderTextLayer
            renderAnnotationLayer
          />
        </Document>
      </div>
    </div>
  );
}

export function CompiledPdfViewer({
  compileStatus,
  getToken,
  fetchPdfBlob,
  scopeId,
  onRequestCompile,
  onRefreshStatus,
}: CompiledPdfViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [compiling, setCompiling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  const revoke = useCallback(() => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
  }, []);

  useEffect(() => () => revoke(), [revoke]);

  useEffect(() => {
    if (compileStatus !== "success") {
      revoke();
      setBlobUrl(null);
      return;
    }
    let cancelled = false;
    setLoadError(null);
    void (async () => {
      try {
        const blob = await fetchPdfBlob(getToken, scopeId);
        if (cancelled) return;
        revoke();
        const url = URL.createObjectURL(blob);
        blobUrlRef.current = url;
        setBlobUrl(url);
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof Error ? err.message : "تعذّر تحميل ملفّ المعاينة.",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [compileStatus, fetchPdfBlob, getToken, revoke, scopeId]);

  useEffect(() => {
    if (compileStatus !== "processing" || !onRefreshStatus) return;
    const id = window.setInterval(() => {
      void onRefreshStatus();
    }, 3000);
    return () => window.clearInterval(id);
  }, [compileStatus, onRefreshStatus]);

  async function handleCompile() {
    if (!onRequestCompile) return;
    setCompiling(true);
    setActionError(null);
    try {
      await onRequestCompile();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "تعذّر بدء إنشاء ملفّ المعاينة.",
      );
    } finally {
      setCompiling(false);
    }
  }

  const busy = compiling || compileStatus === "processing";
  const statusText = STATUS_COPY[compileStatus];

  return (
    <div className="rounded-xl border border-[var(--journal-border)] bg-white/80 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--journal-border)] px-4 py-3">
        <div>
          <h3 className="text-sm font-bold text-[var(--journal-accent)]">
            ملفّ المعاينة
          </h3>
          {statusText ? (
            <p className="mt-1 text-xs leading-6 text-slate-500">{statusText}</p>
          ) : null}
        </div>
        {onRequestCompile ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleCompile()}
            className="min-h-10 rounded-md bg-[var(--journal-accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy
              ? "جارٍ الإنشاء…"
              : compileStatus === "success"
                ? "إعادة إنشاء ملفّ المعاينة"
                : "إنشاء ملفّ المعاينة"}
          </button>
        ) : null}
      </div>

      {actionError || loadError ? (
        <p
          className="mx-4 mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {actionError ?? loadError}
        </p>
      ) : null}

      {compileStatus === "success" && blobUrl ? (
        <PdfPages fileUrl={blobUrl} />
      ) : compileStatus === "processing" ? (
        <p className="px-4 py-10 text-center text-sm text-slate-500">
          يُرجى الانتظار أثناء إنشاء ملفّ المعاينة…
        </p>
      ) : (
        <p className="px-4 py-10 text-center text-sm text-slate-500">
          {onRequestCompile
            ? "اضغط «إنشاء ملفّ المعاينة» لمعاينة المخطوطة كملف مطبوع."
            : "لا يتوفر ملفّ معاينة لهذا الإصدار بعد."}
        </p>
      )}
    </div>
  );
}
