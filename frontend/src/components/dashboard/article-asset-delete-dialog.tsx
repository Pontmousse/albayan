"use client";

import { AlertTriangle, Trash2, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useOpenTransition } from "@/hooks/use-open-transition";

const DELETE_DIALOG_EXIT_MS = 220;

export function ArticleAssetDeleteDialog({
  open,
  assetLabel,
  deleting,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  assetLabel: string;
  deleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { mounted, visible } = useOpenTransition(open, DELETE_DIALOG_EXIT_MS);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!visible) return;
    const frame = requestAnimationFrame(() => cancelButtonRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [visible]);

  useEffect(() => {
    if (!visible) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape" || deleting) return;
      event.preventDefault();
      onCancel();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [deleting, onCancel, visible]);

  if (!mounted) return null;

  const durationMs = visible ? 280 : DELETE_DIALOG_EXIT_MS;

  return (
    <div
      className={`fixed inset-0 z-[80] flex items-end justify-center p-0 transition-opacity motion-reduce:transition-none sm:items-center sm:p-4 ${
        visible ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
      style={{
        transitionDuration: `${durationMs}ms`,
        transitionTimingFunction: visible
          ? "var(--motion-ease-out)"
          : "var(--motion-ease-in)",
      }}
    >
      <button
        type="button"
        aria-label="إلغاء حذف الصورة"
        tabIndex={-1}
        disabled={deleting}
        onClick={onCancel}
        className="absolute inset-0 bg-slate-950/45 backdrop-blur-[3px] disabled:cursor-wait"
      />

      <section
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="asset-delete-dialog-title"
        aria-describedby="asset-delete-dialog-description"
        className={`relative w-full max-w-md overflow-hidden rounded-t-3xl border border-[var(--journal-border)] bg-[var(--journal-paper)] shadow-2xl transition-[transform,opacity] motion-reduce:translate-y-0 motion-reduce:scale-100 motion-reduce:opacity-100 motion-reduce:transition-none sm:rounded-3xl ${
          visible
            ? "translate-y-0 scale-100 opacity-100"
            : "translate-y-4 scale-[0.985] opacity-0 sm:translate-y-2"
        }`}
        style={{
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: visible
            ? "var(--motion-ease-out)"
            : "var(--motion-ease-in)",
        }}
      >
        <div className="h-1 bg-[var(--journal-gold)]" />
        <div className="p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-red-200 bg-red-50 text-red-700 shadow-sm">
              <AlertTriangle aria-hidden className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold tracking-wide text-[var(--journal-gold)]">
                    تأكيد الحذف
                  </p>
                  <h2
                    id="asset-delete-dialog-title"
                    className="mt-1 text-xl font-bold text-slate-900"
                    style={{ fontFamily: "var(--font-display-ar), serif" }}
                  >
                    حذف الصورة من مخزون المقال؟
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={onCancel}
                  disabled={deleting}
                  aria-label="إلغاء"
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 disabled:opacity-50"
                >
                  <X aria-hidden className="h-4 w-4" />
                </button>
              </div>

              <p
                id="asset-delete-dialog-description"
                className="mt-3 text-sm leading-7 text-slate-600"
              >
                سيتم حذف
                {" "}
                <strong className="font-semibold text-slate-800" dir="auto">
                  «{assetLabel}»
                </strong>
                {" "}
                نهائياً من صور المقال. هذه الصورة غير مستخدمة حالياً داخل المستند،
                ولا يمكن التراجع عن الحذف بعد تأكيده.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <button
              ref={cancelButtonRef}
              type="button"
              onClick={onCancel}
              disabled={deleting}
              className="inline-flex min-h-12 items-center justify-center rounded-xl border border-[var(--journal-border)] bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 disabled:cursor-wait disabled:opacity-60"
            >
              إلغاء
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={deleting}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-red-700 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-red-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300 disabled:cursor-wait disabled:opacity-70"
            >
              <Trash2 aria-hidden className="h-4 w-4" />
              {deleting ? "جارٍ الحذف…" : "حذف الصورة"}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
