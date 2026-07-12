"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { adminSections } from "@/lib/admin-config";

function isActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-3 py-5 sm:gap-6 sm:px-6 sm:py-8 lg:flex-row lg:gap-10 lg:px-6 lg:py-12">
        <aside className="sticky top-[3.25rem] z-20 -mx-3 shrink-0 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 px-3 py-2 backdrop-blur-sm sm:top-[3.75rem] sm:-mx-0 sm:border-0 sm:bg-transparent sm:px-0 sm:py-0 sm:backdrop-blur-none lg:static lg:w-52">
          <p className="mb-1.5 hidden px-1 text-xs font-semibold tracking-wide text-[var(--journal-muted)] sm:block lg:mb-2">
            لوحة الإدارة
          </p>
          <nav
            aria-label="أقسام الإدارة"
            className="nav-scroll flex gap-1 overflow-x-auto pb-0.5 lg:flex-col lg:gap-0.5 lg:overflow-visible"
          >
            {adminSections.map((section) => {
              const active = isActive(pathname, section.href);
              return (
                <Link
                  key={section.id}
                  href={section.href}
                  aria-current={active ? "page" : undefined}
                  className={`inline-flex min-h-10 shrink-0 snap-start items-center whitespace-nowrap rounded-md px-3 text-sm font-medium transition-colors duration-150 ${
                    active
                      ? "bg-[var(--journal-accent)] text-white"
                      : "text-slate-700 active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
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
