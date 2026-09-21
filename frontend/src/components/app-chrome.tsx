"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

/** Paths that must stay focused (no journal nav chrome). */
function isMinimalChromePath(pathname: string): boolean {
  return pathname === "/oauth-consent" || pathname.startsWith("/oauth-consent/");
}

/**
 * Authoring is a focused workspace with its own compact Al Bayan editor header.
 * Keep the normal site masthead/footer out of the route instead of hiding them
 * after render so BuTeX receives the full available viewport.
 */
function isEditorChromePath(pathname: string): boolean {
  return /^\/maktabi\/maqalati\/[^/]+\/tahrir\/?$/.test(pathname);
}

/**
 * Global journal chrome. Focused flows render their own purpose-built shell;
 * all normal journal pages retain the standard header and footer.
 */
export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isMinimalChromePath(pathname) || isEditorChromePath(pathname)) {
    return <div className="flex min-h-screen flex-1 flex-col">{children}</div>;
  }

  return (
    <div className="flex flex-1 flex-col">
      <SiteHeader />
      {children}
      <SiteFooter />
    </div>
  );
}
