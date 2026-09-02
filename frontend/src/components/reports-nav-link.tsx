import { MessageSquareWarning } from "lucide-react";
import Link from "next/link";

export function ReportsNavLink() {
  return (
    <Link
      href="/balaghat"
      className="nav-feature-link nav-feature-link--reports group"
    >
      <span className="nav-feature-link__icon" aria-hidden>
        <MessageSquareWarning strokeWidth={1.9} />
      </span>
      <span className="nav-feature-link__label">البلاغات</span>
    </Link>
  );
}
