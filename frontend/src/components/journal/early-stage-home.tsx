import Link from "next/link";
import { HomeHeroCtas } from "@/components/journal/home-hero-ctas";
import { isMcpEnabled } from "@/lib/mcp-enabled";

type EarlyStageHomeProps = {
  signedIn: boolean;
};

/**
 * واجهة الرئيسية عندما published_count = 0.
 * للزوّار: مجلة في طور إعداد أولى إصداراتها — بلا بيانات مختلقة.
 * للوكلاء: لا تُذكر قاعدة البيانات أو التحويل التلقائي أو ISSN في النص الظاهر.
 */
export function EarlyStageHome({ signedIn }: EarlyStageHomeProps) {
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
            <HomeHeroCtas
              variant="early"
              mcpEnabled={mcpEnabled}
              initialSignedIn={signedIn}
            />
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
              {". والنشر في هذه المرحلة بلا رسوم على المؤلفين، وبيان ذلك في "}
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
