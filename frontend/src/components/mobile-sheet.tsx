"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

const EXIT_MS = 280;

export function MobileSheet({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [mounted, setMounted] = useState(open);
  const [visible, setVisible] = useState(open);

  useEffect(() => {
    if (open) {
      setMounted(true);
      const frame = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(frame);
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
    if (visible) closeRef.current?.focus();
  }, [visible]);

  if (!mounted) return null;

  return createPortal(
    <div
      className={`fixed inset-0 z-[60] flex flex-col bg-[var(--journal-paper)] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] transition-[opacity,transform] duration-300 ease-out motion-reduce:transition-none ${
        visible
          ? "opacity-100 translate-y-0 scale-100"
          : "opacity-0 translate-y-3 scale-[0.985]"
      }`}
      style={{ transitionDuration: `${EXIT_MS}ms` }}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onPointerDown={(event) => event.stopPropagation()}
    >
      <div
        className={`flex items-center justify-between gap-3 border-b border-emerald-200/80 bg-gradient-to-l from-emerald-50/90 to-[var(--journal-paper)] px-4 py-3 transition-[opacity,transform] ease-out motion-reduce:transition-none ${
          visible
            ? "opacity-100 translate-y-0"
            : "opacity-0 -translate-y-1"
        }`}
        style={{ transitionDuration: `${EXIT_MS}ms` }}
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
        className={`min-h-0 flex-1 overflow-y-auto overscroll-contain transition-[opacity,transform] ease-out motion-reduce:transition-none ${
          visible
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-2"
        }`}
        style={{
          transitionDuration: `${EXIT_MS}ms`,
          transitionDelay: visible ? "40ms" : "0ms",
        }}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
