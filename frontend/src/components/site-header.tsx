import Link from "next/link";
import { AuthHeader } from "@/components/auth-header";
import { MainNav } from "@/components/main-nav";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-amber-200/90 bg-[var(--journal-paper)]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <Link
          href="/"
          className="group inline-flex flex-col gap-0.5 transition-opacity duration-200 hover:opacity-90"
        >
          <span
            className="text-2xl font-bold tracking-tight text-[var(--journal-accent)] transition-colors duration-200 group-hover:text-[var(--journal-accent-strong)] sm:text-3xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            البيان
          </span>
          <span className="text-xs font-medium text-slate-500">
            مجلة علمية محكّمة · نشر مفتوح مجاني
          </span>
        </Link>
        <div className="flex flex-col items-end gap-3 sm:flex-row sm:items-center sm:gap-4">
          <MainNav />
          <AuthHeader />
        </div>
      </div>
    </header>
  );
}
