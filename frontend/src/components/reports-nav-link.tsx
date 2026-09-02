import { MessageSquareWarning } from "lucide-react";
import Link from "next/link";

export function ReportsNavLink({
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
      href="/balaghat"
      onClick={onClick}
      aria-label={compact && !inMenu ? "الانتقال إلى البلاغات" : undefined}
      className={`nav-feature-link nav-feature-link--reports group ${
        compact ? "nav-feature-link--compact" : ""
      } ${inMenu ? "nav-feature-link--menu" : ""}`}
    >
      <span className="nav-feature-link__icon" aria-hidden>
        <MessageSquareWarning strokeWidth={1.9} />
      </span>
      <span className="nav-feature-link__label">البلاغات</span>
    </Link>
  );
}
