import Link from "next/link";

export function SimplePageFooter() {
  return (
    <footer className="mt-auto border-t border-amber-200 bg-[#eadfca]">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-sm text-slate-600 sm:px-6">
        <Link href="/" className="font-semibold text-[var(--journal-accent)] hover:underline">
          العودة إلى الرئيسية
        </Link>
        <span>© ١٤٤٧ هـ مجلة البيان</span>
      </div>
    </footer>
  );
}
