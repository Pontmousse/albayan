"use client";

import { useUser } from "@clerk/nextjs";
import { Heart } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { AdminNavLink } from "@/components/admin-nav-link";
import { AgentsNavLink } from "@/components/agents-nav-link";
import { mobileSheetOptionClassName } from "@/components/mobile-sheet";
import { NumeralToggle } from "@/components/numeral-toggle";
import { ReportsNavLink } from "@/components/reports-nav-link";
import { readClerkRole } from "@/lib/clerk-role";
import { isMcpEnabled } from "@/lib/mcp-enabled";
import {
  contactNavLink,
  navGroups,
  primaryNavLink,
  supportNavLink,
} from "@/lib/nav-config";

export function MobileNavigationContent({
  onNavigate,
  contextualContent,
}: {
  onNavigate: () => void;
  contextualContent?: ReactNode;
}) {
  const { user } = useUser();
  const isAdmin = readClerkRole(user?.publicMetadata) === "admin";
  const flatLinks = [
    primaryNavLink,
    ...navGroups.flatMap((group) => group.items),
    contactNavLink,
  ];

  return (
    <div className="flex flex-col">
      <div className="border-b border-[var(--journal-border)]">
        <NumeralToggle mobile />
      </div>

      {contextualContent ? (
        <div className="border-b border-[var(--journal-border)]">
          {contextualContent}
        </div>
      ) : null}

      <div className="flex gap-2 border-b border-[var(--journal-border)] bg-[var(--journal-accent-soft)]/35 px-4 py-3">
        <ReportsNavLink inMenu onClick={onNavigate} />
        {isAdmin ? <AdminNavLink inMenu onClick={onNavigate} /> : null}
        {isMcpEnabled() ? <AgentsNavLink inMenu onClick={onNavigate} /> : null}
      </div>

      <div className="border-b border-[var(--journal-border)] px-4 py-3">
        <Link
          href={supportNavLink.href}
          onClick={onNavigate}
          aria-label="دعم مجلة البيان"
          className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[var(--journal-accent)] px-4 text-sm font-bold text-white shadow-sm transition hover:bg-[var(--journal-accent-strong)] active:bg-[var(--journal-accent-strong)]"
        >
          <Heart aria-hidden className="h-4 w-4 shrink-0" />
          <span>{supportNavLink.label}</span>
        </Link>
      </div>

      <ul className="py-1">
        {flatLinks.map((item) => (
          <li key={item.href} role="none">
            <Link
              href={item.href}
              role="menuitem"
              onClick={onNavigate}
              className={`${mobileSheetOptionClassName} text-slate-700 active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]`}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
