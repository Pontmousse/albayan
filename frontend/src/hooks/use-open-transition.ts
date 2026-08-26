"use client";

import { useEffect, useState } from "react";

/**
 * Two-phase open/close so CSS transitions can run:
 * `mounted` keeps the node in the DOM during exit; `visible` drives the animation.
 */
export function useOpenTransition(open: boolean, exitMs: number) {
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
    const timer = window.setTimeout(() => setMounted(false), exitMs);
    return () => window.clearTimeout(timer);
  }, [open, exitMs]);

  return { mounted, visible };
}
