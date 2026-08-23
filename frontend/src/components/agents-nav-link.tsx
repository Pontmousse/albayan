"use client";

import Link from "next/link";

export function AgentsNavLink() {
  return (
    <Link
      href="/wukala"
      className="agents-nav-link group inline-flex min-h-10 items-center gap-1.5 rounded-full border border-emerald-500/45 bg-gradient-to-br from-emerald-50/90 to-white px-3 py-1 text-sm font-semibold text-emerald-900 shadow-sm transition-shadow duration-300 hover:shadow-md"
    >
      <span
        className="agents-nav-link__plus inline-flex h-5 w-5 items-center justify-center rounded-full bg-[var(--journal-accent)] text-xs font-bold text-white"
        aria-hidden
      >
        +
      </span>
      <span>وكلاء</span>
      <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-900">
        DEV
      </span>
    </Link>
  );
}
