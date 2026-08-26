"use client";

import { useState } from "react";

export function CopyButton({
  value,
  ariaLabel = "نسخ",
  className = "",
}: {
  value: string;
  ariaLabel?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      onClick={() => void handleCopy()}
      aria-label={copied ? "تم النسخ" : ariaLabel}
      data-copied={copied ? "true" : "false"}
      className={`copy-button inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] ${className}`}
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {copied ? (
          <path d="M5 13l4 4L19 7" />
        ) : (
          <>
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </>
        )}
      </svg>
    </button>
  );
}
