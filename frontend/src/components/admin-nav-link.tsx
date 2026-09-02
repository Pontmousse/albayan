"use client";

import { useUser } from "@clerk/nextjs";
import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { readClerkRole } from "@/lib/clerk-role";

export function AdminNavLink({
  compact = false,
  inMenu = false,
  onClick,
}: {
  compact?: boolean;
  inMenu?: boolean;
  onClick?: () => void;
}) {
  const { user } = useUser();

  if (readClerkRole(user?.publicMetadata) !== "admin") return null;

  return (
    <Link
      href="/admin"
      onClick={onClick}
      aria-label={compact && !inMenu ? "الانتقال إلى الإدارة" : undefined}
      className={`nav-feature-link nav-feature-link--admin group ${
        compact ? "nav-feature-link--compact" : ""
      } ${inMenu ? "nav-feature-link--menu" : ""}`}
    >
      <span className="nav-feature-link__icon" aria-hidden>
        <ShieldCheck strokeWidth={1.9} />
      </span>
      <span className="nav-feature-link__label">الإدارة</span>
    </Link>
  );
}
