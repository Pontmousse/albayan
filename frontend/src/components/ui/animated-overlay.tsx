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
  mobileFullscreen = false,
}: {
  open: boolean;
  onClose: () => void;
  labelledBy?: string;
  children: ReactNode;
  panelClassName?: string;
  /**
   * Use a deterministic viewport-height surface on phones while retaining a
   * centered dialog from the tablet breakpoint upward. Consumers still own
   * their internal header/body/footer layout and scroll strategy.
   */
  mobileFullscreen?: boolean;
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

  const viewportClassName = mobileFullscreen
    ? "items-stretch p-0 md:items-center md:p-4"
    : "items-end p-0 sm:items-center sm:p-4";
  const panelSurfaceClassName = mobileFullscreen
    ? "h-[100dvh] max-h-[100dvh] rounded-none border-0 p-0 md:h-auto md:max-h-[calc(100dvh-2rem)] md:rounded-2xl md:border md:p-6"
    : "rounded-t-2xl border p-5 sm:rounded-2xl sm:p-6 pb-[max(1.25rem,env(safe-area-inset-bottom))]";

  return (
    <div
      className={`fixed inset-0 z-50 flex justify-center ${viewportClassName}`}
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
        className={`relative w-full max-w-md border-[var(--journal-border)] bg-[var(--journal-paper)] shadow-xl outline-none motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none ${panelSurfaceClassName} ${
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
        {mobileFullscreen ? (
          <span
            aria-hidden="true"
            className="block h-[env(safe-area-inset-top)] shrink-0 md:hidden"
          />
        ) : null}
        {children}
        {mobileFullscreen ? (
          <span
            aria-hidden="true"
            className="block h-[env(safe-area-inset-bottom)] shrink-0 md:hidden"
          />
        ) : null}
      </div>
    </div>
  );
}
