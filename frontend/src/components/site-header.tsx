import Link from "next/link";
import Image from "next/image";
import { AuthHeader } from "@/components/auth-header";
import { MainNav } from "@/components/main-nav";

export function SiteHeader() {
  return (
    <header
      data-site-header
      className="sticky top-0 z-40 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 pt-[env(safe-area-inset-top)] backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-3 py-2.5 sm:gap-4 sm:px-6 sm:py-3 lg:px-8">
        <Link
          href="/"
          className="group flex min-w-0 shrink-0 items-center gap-2 transition-opacity duration-200 hover:opacity-90 sm:gap-2.5"
        >
          <span className="albayan-logo-sweep relative block h-12 w-12 shrink-0 overflow-hidden rounded-full sm:h-16 sm:w-16">
            <Image
              src="/official-logo.png"
              alt=""
              width={64}
              height={64}
              priority
              className="h-full w-full object-contain"
            />
          </span>
          <span className="min-w-0">
            <span
              className="block text-xl font-bold leading-tight tracking-tight text-[var(--journal-accent)] transition-colors duration-200 group-hover:text-[var(--journal-accent-strong)] sm:text-3xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              مجلة البيان
            </span>
            <span className="mt-0.5 hidden text-xs font-medium text-slate-500 sm:block">
              مجلة علمية محكّمة
            </span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center justify-end gap-1.5 sm:gap-3">
          <MainNav />
          <div
            className="hidden h-5 w-px shrink-0 bg-[var(--journal-border)] sm:block"
            aria-hidden
          />
          <AuthHeader />
        </div>
      </div>
    </header>
  );
}
