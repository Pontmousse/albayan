"use client";

import { Bot } from "lucide-react";
import Link from "next/link";

export function AgentsNavLink({
  compact = false,
  inMenu = false,
  onClick,
}: {
  compact?: boolean;
  inMenu?: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href="/wukala"
      onClick={onClick}
      aria-label={compact && !inMenu ? "الانتقال إلى صفحة الوكلاء" : undefined}
      className={`nav-feature-link nav-feature-link--agents group ${
        compact ? "nav-feature-link--compact" : ""
      } ${inMenu ? "nav-feature-link--menu" : ""}`}
    >
      <span className="nav-feature-link__icon" aria-hidden>
        <Bot strokeWidth={1.9} />
      </span>
      <span className="nav-feature-link__label">وكلاء</span>
    </Link>
  );
}
