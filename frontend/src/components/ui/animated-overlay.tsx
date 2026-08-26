"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { useOpenTransition } from "@/hooks/use-open-transition";

export const OVERLAY_ENTER_MS = 320;
export const OVERLAY_EXIT_MS = 280;

export function AnimatedOverlay({
  open,
  onClose,
  labelledBy,
  children,
  panelClassName = "",
}: {
  open: boolean;
  onClose: () => void;
  labelledBy?: string;
  children: ReactNode;
  panelClassName?: string;
}) {
  const { mounted, visible } = useOpenTransition(open, OVERLAY_EXIT_MS);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!mounted) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mounted]);

  useEffect(() => {
    if (visible) panelRef.current?.focus();
  }, [visible]);

  if (!mounted) return null;

  const durationMs = visible ? OVERLAY_ENTER_MS : OVERLAY_EXIT_MS;
  const easing = visible
    ? "var(--motion-ease-out)"
    : "var(--motion-ease-in)";

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelledBy}
    >
      <button
        type="button"
        aria-label="إغلاق"
        tabIndex={-1}
        className={`absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] motion-reduce:transition-none ${
          visible ? "opacity-100" : "opacity-0"
        }`}
        style={{
          transitionProperty: "opacity",
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: easing,
        }}
        onClick={onClose}
      />
      <div
        ref={panelRef}
        tabIndex={-1}
        className={`relative w-full max-w-md rounded-t-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)] p-5 shadow-xl outline-none motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none sm:rounded-2xl sm:p-6 pb-[max(1.25rem,env(safe-area-inset-bottom))] ${
          visible
            ? "translate-y-0 opacity-100"
            : "translate-y-3 opacity-0 sm:translate-y-2"
        } ${panelClassName}`}
        style={{
          transitionProperty: "translate, opacity",
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: easing,
        }}
      >
        {children}
      </div>
    </div>
  );
}
