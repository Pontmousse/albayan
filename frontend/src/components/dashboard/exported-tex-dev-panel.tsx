"use client";

import { useEffect, useState } from "react";
import { DocumentJsonDevDialog } from "@/components/dashboard/document-json-dev-dialog";
import {
  fetchArticleCompileLog,
  type VersionRead,
} from "@/lib/api/articles";
import { exportDocumentLatex } from "@/lib/butex-latex";
import { isDevMode } from "@/lib/dev-mode";

type GetToken = () => Promise<string | null>;

type Props = {
  documentJson: unknown;
  /** لقطة TeX كما أُرسلت في آخر طلب compile — إن وُجدت تُفضَّل على إعادة التصدير. */
  texSnapshot?: string | null;
  compileStatus: VersionRead["compile_status"];
  articleId: string;
  getToken: GetToken;
};

export function ExportedTexDevPanel({
  documentJson,
  texSnapshot,
  compileStatus,
  articleId,
  getToken,
}: Props) {
  const [liveTex, setLiveTex] = useState("");
  const [exportError, setExportError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [compileLog, setCompileLog] = useState<string | null>(null);
  const [logError, setLogError] = useState<string | null>(null);
  const [jsonOpen, setJsonOpen] = useState(false);

  useEffect(() => {
    if (!isDevMode()) return;
    if (documentJson == null) {
      setLiveTex("");
      setExportError(null);
      return;
    }
    try {
      setLiveTex(exportDocumentLatex(documentJson));
      setExportError(null);
    } catch (err) {
      setLiveTex("");
      setExportError(
        err instanceof Error ? err.message : "تعذّر تصدير المخطوطة إلى TeX.",
      );
    }
  }, [documentJson]);

  useEffect(() => {
    if (!isDevMode() || compileStatus !== "failed") {
      setCompileLog(null);
      setLogError(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const { log } = await fetchArticleCompileLog(getToken, articleId);
        if (!cancelled) {
          setCompileLog(log);
          setLogError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setCompileLog(null);
          setLogError(
            err instanceof Error
              ? err.message
              : "تعذّر جلب سجل الترجمة.",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [compileStatus, articleId, getToken]);

  if (!isDevMode()) return null;

  const tex =
    texSnapshot != null && texSnapshot.length > 0 ? texSnapshot : liveTex;

  async function handleCopy() {
    if (!tex) return;
    try {
      await navigator.clipboard.writeText(tex);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="mt-4 rounded-xl border border-amber-300/80 bg-amber-50/60 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-amber-200 px-4 py-3">
        <h3 className="text-sm font-bold text-amber-900">
          تطوير / TeX المُصدَّر
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setJsonOpen(true)}
            className="min-h-9 rounded-md border border-amber-400 bg-white px-3 text-xs font-semibold text-amber-900 transition hover:bg-amber-100"
          >
            See JSON
          </button>
          <button
            type="button"
            disabled={!tex}
            onClick={() => void handleCopy()}
            className="min-h-9 rounded-md border border-amber-400 bg-white px-3 text-xs font-semibold text-amber-900 transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {copied ? "تم النسخ" : "نسخ TeX"}
          </button>
        </div>
      </div>

      {exportError ? (
        <p className="mx-4 mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {exportError}
        </p>
      ) : null}

      <pre
        dir="ltr"
        className="mx-4 my-3 max-h-96 overflow-auto rounded-md border border-amber-200 bg-white p-3 text-start font-mono text-xs leading-5 text-slate-800 whitespace-pre-wrap"
      >
        {tex || "(لا يوجد TeX بعد — احفظ المخطوطة أو أنشئ ملفّ المعاينة.)"}
      </pre>

      {compileStatus === "failed" ? (
        <div className="border-t border-amber-200 px-4 py-3">
          <h4 className="text-xs font-bold text-amber-900">سجل الترجمة</h4>
          {logError ? (
            <p className="mt-2 text-sm text-red-700" role="alert">
              {logError}
            </p>
          ) : compileLog != null ? (
            <pre
              dir="ltr"
              className="mt-2 max-h-64 overflow-auto rounded-md border border-red-200 bg-white p-3 text-start font-mono text-xs leading-5 text-slate-800 whitespace-pre-wrap"
            >
              {compileLog}
            </pre>
          ) : (
            <p className="mt-2 text-xs text-slate-500">جارٍ جلب السجل…</p>
          )}
        </div>
      ) : null}

      <DocumentJsonDevDialog
        open={jsonOpen}
        value={documentJson}
        onClose={() => setJsonOpen(false)}
      />
    </div>
  );
}
