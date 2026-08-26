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
 * Global journal chrome. OAuth consent uses a bare shell so the authorization
 * decision is not diluted by navigation or account menus.
 */
export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isMinimalChromePath(pathname)) {
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
