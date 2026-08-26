"use client";

import { useState } from "react";
import {
  CHATGPT_DETAILED_GUIDE,
  type ChatGptDetailedStep,
} from "@/lib/mcp-client-guides";

function CopyValue({ step }: { step: ChatGptDetailedStep }) {
  const [copied, setCopied] = useState(false);

  if (!step.copyValue) return null;

  async function handleCopy() {
    if (!step.copyValue) return;
    try {
      await navigator.clipboard.writeText(step.copyValue);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <span className="mt-1.5 flex flex-wrap items-center gap-2">
      <code
        dir="auto"
        className="min-w-0 break-all rounded-md bg-slate-100 px-2.5 py-1.5 text-start text-xs text-slate-800"
      >
        {step.copyValue}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-md border border-[var(--journal-border)] bg-white px-2.5 py-1 text-xs font-semibold text-[var(--journal-accent-strong)] transition hover:border-[var(--journal-accent)]"
      >
        {copied ? "تم النسخ" : step.copyLabel ?? "نسخ"}
      </button>
    </span>
  );
}

/** دليل ChatGPT التفصيلي — مطويّ افتراضياً حتى لا يُثقل الصفحة على غير المتقدمين. */
export function ChatGptDetailedGuide() {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-4 rounded-xl border border-[var(--journal-border)] bg-white/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-start"
      >
        <span>
          <span className="block text-sm font-bold text-slate-900">
            الدليل التفصيلي خطوة بخطوة
          </span>
          <span className="mt-0.5 block text-xs text-slate-600">
            كل خطوات ChatGPT من تفعيل وضع المطوّر حتى «السماح» — مع أزرار نسخ
          </span>
        </span>
        <span
          aria-hidden
          className={`shrink-0 text-slate-500 transition-transform ${
            open ? "rotate-90" : ""
          }`}
        >
          ‹
        </span>
      </button>

      {open && (
        <div className="border-t border-[var(--journal-border)] px-4 py-4">
          <ol className="space-y-5">
            {CHATGPT_DETAILED_GUIDE.map((section) => (
              <li key={section.title}>
                <h4 className="text-sm font-bold text-[var(--journal-accent-strong)]">
                  {section.title}
                </h4>
                <ol className="mt-2 list-decimal space-y-2.5 ps-5 text-sm leading-6 text-slate-700">
                  {section.steps.map((step) => (
                    <li key={step.text}>
                      {step.text}
                      <CopyValue step={step} />
                    </li>
                  ))}
                </ol>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
