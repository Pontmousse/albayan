"use client";

import Link from "next/link";

export function AgentsNavLink({
  onClick,
}: {
  onClick?: () => void;
}) {
  return (
    <Link
      href="/wukala"
      onClick={onClick}
      className="agents-nav-link group inline-flex min-h-10 items-center gap-1.5 rounded-full border border-emerald-500/45 bg-gradient-to-br from-emerald-50/90 to-white px-2.5 py-1 text-xs font-semibold text-emerald-900 shadow-sm transition-shadow duration-300 hover:shadow-md sm:px-3 sm:text-sm"
    >
      <span
        className="agents-nav-link__plus inline-flex h-5 w-5 items-center justify-center rounded-full bg-[var(--journal-accent)] text-xs font-bold text-white"
        aria-hidden
      >
        +
      </span>
      <span>وكلاء</span>
    </Link>
  );
}
