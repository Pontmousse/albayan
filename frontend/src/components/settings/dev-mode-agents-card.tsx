import Link from "next/link";
import { cardClassName } from "@/lib/auth-ui";
import { isDevMode } from "@/lib/dev-mode";

export function DevModeAgentsCard() {
  if (!isDevMode()) {
    return null;
  }

  return (
    <section
      className={`${cardClassName} mt-8 border-emerald-200/80 bg-gradient-to-br from-emerald-50/80 to-white`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">
            وضع تطوير
          </p>
          <h2 className="mt-1 text-lg font-bold text-slate-900">مفاتيح الوكلاء</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">
            أنشئ مفتاحاً شخصياً لربط وكيلك الذكي (MCP) بمنصة البيان — للكتابة
            بمساعدة الوكيل مع الحفظ اليدوي.
          </p>
        </div>
        <Link
          href="/al-idayat/wukala"
          className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
        >
          إدارة المفاتيح
        </Link>
      </div>
    </section>
  );
}
