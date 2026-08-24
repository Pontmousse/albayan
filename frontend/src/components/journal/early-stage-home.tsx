import Link from "next/link";
import { isMcpEnabled } from "@/lib/mcp-enabled";

/**
 * واجهة الرئيسية عندما published_count = 0.
 * تعكس الحالة الحقيقية: منصة قيد الإعداد بلا منشورات بعد.
 */
export function EarlyStageHome() {
  const mcpEnabled = isMcpEnabled();

  return (
    <>
      <section className="border-b border-[var(--journal-border)] bg-[linear-gradient(180deg,var(--journal-accent-soft)_0%,var(--journal-paper)_100%)]">
        <div className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8 lg:py-14">
          <div className="mx-auto max-w-3xl space-y-6 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              منصة قيد الإعداد
            </p>
            <h1
              className="text-balance text-2xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              مجلة البيان — نشر علمي عربي رصين
            </h1>
            <p className="text-pretty text-sm leading-relaxed text-slate-600 sm:text-lg">
              نعمل حاليًا على إعداد أول منشورات البيان وبناء منصة النشر والتحكيم.
              المنصة متاحة للتجربة والتطوير، ولم تُنشر بعد مقالات رسمية في الواجهة
              العامة.
            </p>
            <div className="flex flex-col items-stretch justify-center gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:gap-3">
              <Link
                href="/irshadat-al-mualifin"
                className="inline-flex min-h-11 items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
              >
                إرشادات المؤلفين
              </Link>
              <Link
                href="/tasjil"
                className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-[var(--journal-accent)]"
              >
                إنشاء حساب
              </Link>
              <Link
                href="/tawajjuh"
                className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-[var(--journal-accent)]"
              >
                تسجيل الدخول
              </Link>
              {mcpEnabled ? (
                <Link
                  href="/wukala"
                  className="inline-flex min-h-11 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 px-5 text-sm font-semibold text-emerald-900 transition hover:border-emerald-300"
                >
                  الوكلاء الذكيون
                </Link>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8">
        <div className="mx-auto max-w-3xl space-y-8">
          <div className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-6 text-center shadow-sm">
            <h2
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              لا منشورات بعد
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              لم تُنشر مقالات في الواجهة العامة حتى الآن. عند اعتماد أول منشورات
              من قاعدة البيانات، ستنتقل هذه الصفحة تلقائيًا إلى عرض المقالات
              المنشورة — دون إعادة تصميم يدوي.
            </p>
          </div>

          <dl className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-[var(--journal-border)] bg-white/70 p-5">
              <dt className="text-xs font-medium text-slate-500">سياسة معتمدة حاليًا</dt>
              <dd className="mt-2 text-sm font-semibold text-slate-900">
                النشر مجاني للمؤلفين في هذه المرحلة
              </dd>
              <dd className="mt-1 text-xs leading-6 text-slate-600">
                انظر{" "}
                <Link href="/siyasat-an-nashr" className="font-semibold text-[var(--journal-accent)] hover:underline">
                  سياسة النشر
                </Link>
              </dd>
            </div>
            <div className="rounded-xl border border-[var(--journal-border)] bg-white/70 p-5">
              <dt className="text-xs font-medium text-slate-500">أهداف مستقبلية</dt>
              <dd className="mt-2 text-sm font-semibold text-slate-900">
                تحكيم أقران، وصول حر، أرشفة دائمة
              </dd>
              <dd className="mt-1 text-xs leading-6 text-slate-600">
                تُفصَّل في السياسات عند الاكتمال — لا نعرض ISSN أو DOI أو أعداد
                وهمية قبل توفرها.
              </dd>
            </div>
          </dl>
        </div>
      </section>
    </>
  );
}
