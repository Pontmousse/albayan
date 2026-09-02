"use client";

import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { readClerkRole } from "@/lib/clerk-role";

export function AdminNavLink({ onClick }: { onClick?: () => void }) {
  const { user } = useUser();

  if (readClerkRole(user?.publicMetadata) !== "admin") return null;

  return (
    <Link
      href="/admin"
      onClick={onClick}
      className="group inline-flex min-h-10 items-center gap-1.5 rounded-full border border-[var(--admin-accent)]/40 bg-gradient-to-br from-[var(--admin-surface-strong)] to-white px-2.5 py-1 text-xs font-semibold text-[var(--admin-accent-strong)] shadow-sm transition-shadow duration-300 hover:shadow-md sm:px-3 sm:text-sm"
    >
      <span
        className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-[var(--admin-accent)] text-xs font-bold text-white"
        aria-hidden
      >
        أ
      </span>
      <span>الإدارة</span>
    </Link>
  );
}
