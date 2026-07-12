"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { listEditorArticles } from "@/lib/api/editor";
import { listMyAssignments } from "@/lib/api/reviews";
import {
  visibleSections,
  type DashboardRole,
} from "@/lib/dashboard-config";

function isActive(pathname: string, href: string): boolean {
  if (href === "/maktabi") return pathname === "/maktabi";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { getToken } = useAuth();
  const [roles, setRoles] = useState<DashboardRole[]>(["author"]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listMyAssignments(getToken).catch(() => []),
      listEditorArticles(getToken).catch(() => []),
    ]).then(([assignments, editorArticles]) => {
      if (cancelled) return;
      const next: DashboardRole[] = ["author"];
      if (assignments.length > 0) next.push("reviewer");
      if (editorArticles.length > 0) next.push("editor");
      setRoles(next);
    });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const sections = visibleSections(roles);

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-3 py-5 sm:gap-6 sm:px-6 sm:py-8 lg:flex-row lg:gap-10 lg:px-6 lg:py-12">
        <aside className="sticky top-[3.25rem] z-20 -mx-3 shrink-0 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 px-3 py-2 backdrop-blur-sm sm:top-[3.75rem] sm:-mx-0 sm:border-0 sm:bg-transparent sm:px-0 sm:py-0 sm:backdrop-blur-none lg:static lg:w-52">
          <nav
            aria-label="أقسام المكتب"
            className="nav-scroll flex gap-1 overflow-x-auto pb-0.5 lg:flex-col lg:gap-0.5 lg:overflow-visible"
          >
            {sections.map((section) => {
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
