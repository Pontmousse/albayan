"use client";

import { useUser } from "@clerk/nextjs";
import Link from "next/link";

import { AdminNavLink } from "@/components/admin-nav-link";
import { AgentsNavLink } from "@/components/agents-nav-link";
import { mobileSheetOptionClassName } from "@/components/mobile-sheet";
import { NumeralToggle } from "@/components/numeral-toggle";
import { ReportsNavLink } from "@/components/reports-nav-link";
import { readClerkRole } from "@/lib/clerk-role";
import { isMcpEnabled } from "@/lib/mcp-enabled";
import {
  journalNavLinks,
  supportNavLink,
  workspaceNavLinks,
} from "@/lib/nav-config";

function NavigationSectionTitle({ children }: { children: string }) {
  return (
    <p className="px-5 pb-1 pt-4 text-xs font-bold text-slate-500">
      {children}
    </p>
  );
}

export function AlBayanNavigationContent({
  onNavigate,
  compact = false,
}: {
  onNavigate: () => void;
  compact?: boolean;
}) {
  const { isSignedIn, user } = useUser();
  const isAdmin = readClerkRole(user?.publicMetadata) === "admin";
  const optionClassName = compact
    ? "flex min-h-11 w-full items-center px-4 py-2.5 text-start text-sm font-medium leading-6 text-slate-700 transition-colors hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
    : `${mobileSheetOptionClassName} text-slate-700 transition-colors active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]`;

  return (
    <div className={compact ? "pb-2" : "flex flex-col"}>
      <div className="border-b border-[var(--journal-border)]">
        {compact ? (
          <div className="flex items-center justify-between gap-3 px-4 py-3">
            <span className="text-xs font-semibold text-slate-600">
              شكل الأرقام
            </span>
            <NumeralToggle />
          </div>
        ) : (
          <NumeralToggle mobile />
        )}
      </div>

      <div className="flex gap-2 border-b border-[var(--journal-border)] bg-[var(--journal-accent-soft)]/35 px-4 py-3">
        <ReportsNavLink inMenu onClick={onNavigate} />
        {isAdmin ? <AdminNavLink inMenu onClick={onNavigate} /> : null}
        {isMcpEnabled() ? <AgentsNavLink inMenu onClick={onNavigate} /> : null}
      </div>

      <div className="border-b border-[var(--journal-border)] px-4 py-3">
        <Link
          href={supportNavLink.href}
          onClick={onNavigate}
          className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[var(--journal-accent)] px-4 text-sm font-bold text-white shadow-sm transition hover:bg-[var(--journal-accent-strong)] active:bg-[var(--journal-accent-strong)]"
        >
          {supportNavLink.label}
        </Link>
      </div>

      {isSignedIn ? (
        <div className="border-b border-[var(--journal-border)]">
          <NavigationSectionTitle>مساحة العمل</NavigationSectionTitle>
          <ul className="pb-2">
            {workspaceNavLinks.map((item) => (
              <li key={item.href} role="none">
                <Link
                  href={item.href}
                  role="menuitem"
                  onClick={onNavigate}
                  className={optionClassName}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <NavigationSectionTitle>مجلة البيان</NavigationSectionTitle>
      <ul className="pb-1">
        {journalNavLinks.map((item) => (
          <li key={item.href} role="none">
            <Link
              href={item.href}
              role="menuitem"
              onClick={onNavigate}
              className={optionClassName}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
