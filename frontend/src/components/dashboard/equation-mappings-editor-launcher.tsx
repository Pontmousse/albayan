"use client";

import { useAuth } from "@clerk/nextjs";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { EquationMappingsPanel } from "@/components/dashboard/equation-mappings-panel";

function editorArticleId(pathname: string): string | null {
  const match = pathname.match(/^\/maktabi\/maqalati\/([^/]+)\/tahrir\/?$/);
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

export function EquationMappingsEditorLauncher() {
  const pathname = usePathname();
  const { getToken } = useAuth();
  const [open, setOpen] = useState(false);
  const articleId = editorArticleId(pathname);

  if (!articleId) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 end-5 z-40 inline-flex min-h-11 items-center gap-2 rounded-full border border-[var(--journal-border)] bg-white px-4 text-sm font-semibold text-slate-700 shadow-lg transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
        title="ضبط اصطلاحات الرموز الرياضية العربية لهذا المقال"
      >
        <span
          aria-hidden
          className="inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-[var(--journal-accent-soft)] px-1.5 font-mono text-xs text-[var(--journal-accent-strong)]"
        >
          x↔س
        </span>
        الرموز الرياضية
      </button>

      <EquationMappingsPanel
        open={open}
        articleId={articleId}
        getToken={getToken}
        onClose={() => setOpen(false)}
      />
    </>
  );
}
