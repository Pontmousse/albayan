import Link from "next/link";
import { buttonClassName } from "@/lib/auth-ui";

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--journal-border)] bg-white/60 px-4 py-10 text-center sm:px-6 sm:py-14">
      <svg
        aria-hidden
        className="h-10 w-10 text-[var(--journal-gold)] sm:h-12 sm:w-12"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
        />
      </svg>
      <h3
        className="mt-4 text-base font-bold text-slate-900 sm:text-lg"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {title}
      </h3>
      <p className="mt-1.5 max-w-md text-sm leading-6 text-slate-600">
        {description}
      </p>
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className={`${buttonClassName} mt-5 inline-flex sm:mt-6`}
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
