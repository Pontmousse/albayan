"use client";

import { useLayoutEffect, useState } from "react";

/** Tailwind `md` — 768px. */
const MD_QUERY = "(min-width: 768px)";

/**
 * True when the viewport is desktop (`md` and up).
 * Starts false to match SSR, then reads matchMedia before paint.
 */
export function useMdUp(): boolean {
  const [mdUp, setMdUp] = useState(false);

  useLayoutEffect(() => {
    const mq = window.matchMedia(MD_QUERY);
    const apply = () => setMdUp(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  return mdUp;
}
