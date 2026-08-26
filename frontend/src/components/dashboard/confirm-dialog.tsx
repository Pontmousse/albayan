"use client";

import { useEffect, useState } from "react";
import { AnimatedOverlay } from "@/components/ui/animated-overlay";
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
  const [snapshot, setSnapshot] = useState({ title, description, confirmLabel });

  useEffect(() => {
    if (open) {
      setSnapshot({ title, description, confirmLabel });
    }
  }, [open, title, description, confirmLabel]);

  return (
    <AnimatedOverlay
      open={open}
      onClose={onCancel}
      labelledBy="confirm-dialog-title"
    >
      <h2
        id="confirm-dialog-title"
        className="text-xl font-bold text-slate-900"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {snapshot.title}
      </h2>
      <p className="mt-3 text-sm leading-7 text-slate-600">{snapshot.description}</p>
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:flex-wrap sm:justify-end sm:gap-3">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] disabled:opacity-60"
        >
          إلغاء
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={submitting}
          className={buttonClassName}
        >
          {submitting ? "جارٍ التحديث…" : snapshot.confirmLabel}
        </button>
      </div>
    </AnimatedOverlay>
  );
}
