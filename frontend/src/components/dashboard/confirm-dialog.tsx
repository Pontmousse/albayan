"use client";

import { useEffect, useRef } from "react";
import { buttonClassName } from "@/lib/auth-ui";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  submitting,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  submitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onCancel();
    }
    document.addEventListener("keydown", onKeyDown);
    panelRef.current?.focus();
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <button
        type="button"
        aria-label="إغلاق"
        onClick={onCancel}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] transition-opacity"
      />
      <div
        ref={panelRef}
        tabIndex={-1}
        className="page-enter relative w-full max-w-md rounded-2xl border border-amber-200 bg-[var(--journal-paper)] p-6 shadow-xl outline-none"
      >
        <h2
          id="confirm-dialog-title"
          className="text-xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          {title}
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-md border border-amber-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] disabled:opacity-60"
          >
            إلغاء
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={submitting}
            className={buttonClassName}
          >
            {submitting ? "جارٍ التحديث…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
