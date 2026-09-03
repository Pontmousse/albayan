"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

/** Enter: clearly visible open motion */
const ENTER_MS = 380;
/** Exit: slightly snappier close */
const EXIT_MS = 300;
const STAGGER_STEP_MS = 65;

export const mobileSheetOptionClassName =
  "flex min-h-16 w-full items-center gap-4 px-5 py-4 text-start text-base font-semibold leading-7";

export function MobileSheet({
  open,
  onClose,
  title,
  children,
  initialFocusRef,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  initialFocusRef?: RefObject<HTMLElement | null>;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [mounted, setMounted] = useState(open);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (open) {
      setMounted(true);
      setVisible(false);
      let frame2 = 0;
      const frame1 = requestAnimationFrame(() => {
        frame2 = requestAnimationFrame(() => setVisible(true));
      });
      return () => {
        cancelAnimationFrame(frame1);
        cancelAnimationFrame(frame2);
      };
    }
    setVisible(false);
    const timer = window.setTimeout(() => setMounted(false), EXIT_MS);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    if (!mounted) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [mounted, onClose]);

  useEffect(() => {
    if (visible) (initialFocusRef?.current ?? closeRef.current)?.focus();
  }, [initialFocusRef, visible]);

  if (!mounted) return null;

  const durationMs = visible ? ENTER_MS : EXIT_MS;
  const easing = visible ? "cubic-bezier(0.22, 1, 0.36, 1)" : "cubic-bezier(0.4, 0, 1, 1)";

  return createPortal(
    <div
      className="fixed inset-0 z-[60] isolate"
      data-state={visible ? "open" : "closed"}
      onPointerDown={(event) => event.stopPropagation()}
    >
      {/* Backdrop — fade + subtle blur */}
      <button
        type="button"
        aria-label="إغلاق"
        tabIndex={-1}
        className={`absolute inset-0 bg-emerald-950/45 backdrop-blur-[3px] motion-reduce:transition-none ${
          visible ? "opacity-100" : "opacity-0"
        }`}
        style={{
          transitionProperty: "opacity",
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: easing,
        }}
        onClick={onClose}
      />

      {/* Panel — slides from start (RTL-aware via translate-x-full) */}
      <div
        className={`fixed inset-0 flex flex-col bg-[var(--journal-paper)] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] shadow-2xl motion-reduce:transition-none ${
          visible
            ? "translate-x-0 opacity-100"
            : "translate-x-full opacity-0 motion-reduce:translate-x-0 motion-reduce:opacity-100"
        }`}
        style={{
          transitionProperty: "translate, opacity",
          transitionDuration: `${durationMs}ms`,
          transitionTimingFunction: easing,
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <div
          className={`flex items-center justify-between gap-3 border-b border-emerald-200/80 bg-gradient-to-l from-emerald-50/90 to-[var(--journal-paper)] px-4 py-3 motion-reduce:transition-none ${
            visible
              ? "translate-y-0 opacity-100"
              : "-translate-y-2 opacity-0 motion-reduce:translate-y-0 motion-reduce:opacity-100"
          }`}
          style={{
            transitionProperty: "translate, opacity",
            transitionDuration: `${durationMs}ms`,
            transitionTimingFunction: easing,
            transitionDelay: visible ? "70ms" : "0ms",
          }}
        >
          <h2
            id={titleId}
            className="text-lg font-bold text-emerald-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="inline-flex min-h-11 items-center rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm font-semibold text-slate-700"
          >
            إغلاق
          </button>
        </div>
        <div
          className="mobile-sheet-stagger min-h-0 flex-1 overflow-y-auto overscroll-contain"
          data-visible={visible ? "true" : "false"}
          style={
            {
              "--mobile-sheet-enter-ms": `${ENTER_MS}ms`,
              "--mobile-sheet-stagger-step": `${STAGGER_STEP_MS}ms`,
            } as CSSProperties
          }
        >
          {children}
        </div>
      </div>
    </div>,
    document.body,
  );
}
