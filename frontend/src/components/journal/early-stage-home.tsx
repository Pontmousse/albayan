import Link from "next/link";
import { isMcpEnabled } from "@/lib/mcp-enabled";

/**
 * واجهة الرئيسية عندما published_count = 0.
 * للزوّار: مجلة في طور إعداد أولى إصداراتها — بلا بيانات مختلقة.
 * للوكلاء: لا تُذكر قاعدة البيانات أو التحويل التلقائي أو ISSN في النص الظاهر.
 */
export function EarlyStageHome() {
  const mcpEnabled = isMcpEnabled();

  return (
    <>
      <section className="border-b border-[var(--journal-border)] bg-[linear-gradient(180deg,var(--journal-accent-soft)_0%,var(--journal-paper)_100%)]">
        <div className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8 lg:py-14">
          <div className="mx-auto max-w-3xl space-y-6 text-center">
            <h1
              className="text-balance text-2xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              مجلة البيان
            </h1>
            <p
              className="text-balance text-base font-semibold text-[var(--journal-accent)] sm:text-xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              نشر علمي عربي رصين
            </p>
            <p className="text-pretty text-sm leading-relaxed text-slate-600 sm:text-lg">
              تسعى «البيان» إلى نشر بحث علمي رصين بالعربية، يراعي التوحيد والنزاهة،
              ويُحكَّم تحكيم أقران، ويُتاح للقارئ بلا رسوم على المؤلفين.
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
        <div className="mx-auto max-w-3xl">
          <div className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-6 text-center shadow-sm sm:p-8">
            <h2
              className="text-xl font-bold text-slate-900 sm:text-2xl"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              العدد الأول يُعدّ
            </h2>
            <p className="mt-4 text-sm leading-8 text-slate-600 sm:text-base">
              تتهيّأ المجلة لإصدار أولى بحوثها، وتفتح باب المساهمة للباحثين.
              نرحّب بالمخطوطات الجادّة وفق{" "}
              <Link
                href="/irshadat-al-mualifin"
                className="font-semibold text-[var(--journal-accent)] hover:underline"
              >
                إرشادات المؤلفين
              </Link>
              . والنشر في هذه المرحلة بلا رسوم على المؤلفين، وبيان ذلك في{" "}
              <Link
                href="/siyasat-an-nashr"
                className="font-semibold text-[var(--journal-accent)] hover:underline"
              >
                سياسة النشر
              </Link>
              .
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
