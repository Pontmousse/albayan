import Link from "next/link";
import { cardClassName } from "@/lib/auth-ui";
import { isAgentKeyUiEnabled } from "@/lib/dev-mode";

export function DevModeAgentsCard() {
  if (!isAgentKeyUiEnabled()) {
    return null;
  }

  return (
    <section
      className={`${cardClassName} mt-10 border-slate-200 bg-slate-50/70`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold tracking-wide text-slate-500">
            أدوات متقدمة — وضع التطوير
          </p>
          <h2 className="mt-1 text-lg font-bold text-slate-900">مفاتيح الوكلاء</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">
            إدارة مفاتيح شخصية للتجارب المحلية والأتمتة غير التفاعلية. الربط
            البعيد مع تسجيل الدخول هو المسار الموصى به للاستخدام المعتاد.
          </p>
        </div>
        <Link
          href="/al-idayat/wukala"
          className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
        >
          إدارة المفاتيح
        </Link>
      </div>
    </section>
  );
}
