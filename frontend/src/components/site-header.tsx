import Link from "next/link";
import { navLinks } from "@/lib/nav-links";

export function SiteHeader() {
  return (
    <header className="border-b border-amber-200 bg-[var(--journal-paper)]/95">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <Link href="/" className="group inline-flex flex-col gap-0.5">
          <span
            className="text-2xl font-bold tracking-tight text-[var(--journal-accent)] sm:text-3xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            البيان
          </span>
          <span className="text-xs font-medium text-slate-500">
            مجلة علمية محكّمة · نشر مفتوح
          </span>
        </Link>
        <nav
          aria-label="التنقل الرئيسي"
          className="flex flex-wrap items-center justify-end gap-x-4 gap-y-2 text-sm font-medium text-slate-700"
        >
          {navLinks.map((item) => {
            const className =
              "rounded-md px-1 py-0.5 text-slate-700 underline-offset-4 transition hover:text-[var(--journal-accent-strong)] hover:underline";
            if (item.href.startsWith("/")) {
              return (
                <Link key={item.label} href={item.href} className={className}>
                  {item.label}
                </Link>
              );
            }
            return (
              <a key={item.label} href={item.href} className={className}>
                {item.label}
              </a>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
