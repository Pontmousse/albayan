"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { visibleSections } from "@/lib/dashboard-config";

function isActive(pathname: string, href: string): boolean {
  if (href === "/maktabi") return pathname === "/maktabi";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const sections = visibleSections();

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:flex-row lg:gap-10 lg:py-12">
        <aside className="shrink-0 lg:w-52">
          <nav
            aria-label="أقسام المكتب"
            className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:gap-1 lg:pb-0"
          >
            {sections.map((section) => {
              const active = isActive(pathname, section.href);
              return (
                <Link
                  key={section.id}
                  href={section.href}
                  aria-current={active ? "page" : undefined}
                  className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-medium transition-all duration-200 ${
                    active
                      ? "bg-[var(--journal-accent)] text-white shadow-sm"
                      : "text-slate-700 hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
                  }`}
                >
                  {section.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
