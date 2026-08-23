import type { Metadata } from "next";
import Link from "next/link";
import { WukalaCtaButton } from "@/components/wukala/wukala-cta-button";
import { CURSOR_MCP_EXAMPLE } from "@/lib/agent-token-config";

export const metadata: Metadata = {
  title: "الوكلاء (MCP) | البيان",
  description:
    "اربط وكيلك الذكي بمجلة البيان عبر بروتوكول MCP — للكتابة بمساعدة الوكيل مع الحفظ والتقديم اليدوي.",
};

const steps = [
  {
    title: "أنشئ مفتاحاً شخصياً",
    body: "من إعدادات حسابك، أنشئ مفتاح وكيل بصلاحيات محددة — يُعرض مرة واحدة فقط.",
  },
  {
    title: "أضف الخادم في Cursor",
    body: "انسخ إعداد MCP إلى Cursor أو Claude Desktop واستبدل المفتاح في المتغيرات.",
  },
  {
    title: "اكتب مع الوكيل — واحفظ أنت",
    body: "الوكيل يعدّل مسودة الجلسة؛ أنت تراجع في المحرر، تحفظ، وتقدّم يدوياً من المنصة.",
  },
];

export default function WukalaPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-14">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
          وضع تطوير · MCP
        </p>
        <h1
          className="mt-3 text-balance text-3xl font-bold text-slate-900 sm:text-4xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          اربط وكيلك الذكي بمجلة البيان
        </h1>
        <p className="mt-4 text-pretty text-sm leading-7 text-slate-600 sm:text-base">
          استخدم Cursor أو Claude Desktop أو أي عميل يدعم{" "}
          <strong className="font-semibold text-slate-800">
            Model Context Protocol (MCP)
          </strong>{" "}
          للكتابة والتحرير بمساعدة الوكيل — مع بقاء قرار الحفظ والتقديم في يدك.
        </p>

        <section className="mt-10 rounded-2xl border border-[var(--journal-border)] bg-white/80 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">ما هو MCP؟</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">
            بروتوكول مفتوح يربط الوكيل الذكي بتطبيقاتك بأمان. بدلاً من نسخ
            المحتوى يدوياً، يتصل الوكيل بمنصة البيان عبر مفتاح شخصي وينفّذ
            إجراءات مسموحة (قراءة، كتابة مسودة، …) ضمن صلاحياتك.
          </p>
        </section>

        <section className="mt-8">
          <h2
            className="text-xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            كيف يعمل؟
          </h2>
          <ol className="mt-4 space-y-4">
            {steps.map((step, index) => (
              <li
                key={step.title}
                className="flex gap-4 rounded-xl border border-[var(--journal-border)] bg-white/70 p-4"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--journal-accent-soft)] text-sm font-bold text-[var(--journal-accent-strong)]">
                  {index + 1}
                </span>
                <div>
                  <h3 className="font-semibold text-slate-900">{step.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {step.body}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <section className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
            <h2 className="text-sm font-bold text-emerald-900">ما يفعله الوكيل</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-emerald-950/80">
              <li>قراءة مقالاتك وحالتها</li>
              <li>الكتابة في مسودة الجلسة (قريباً بالكامل)</li>
              <li>مسودة ملاحظات المراجعة للمراجعين</li>
            </ul>
          </section>
          <section className="rounded-xl border border-amber-200 bg-amber-50/50 p-5">
            <h2 className="text-sm font-bold text-amber-900">ما لا يفعله</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-950/80">
              <li>تقديم المقال نيابة عنك</li>
              <li>إرسال تقرير المراجعة</li>
              <li>قرارات التحرير أو الإدارة</li>
            </ul>
          </section>
        </div>

        <div className="mt-10 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <WukalaCtaButton className="w-full sm:w-auto" />
          <Link
            href="/irshadat-al-mualifin"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)]"
          >
            إرشادات المؤلفين
          </Link>
        </div>

        <section className="mt-10">
          <h2 className="text-lg font-bold text-slate-900">مثال إعداد Cursor</h2>
          <p className="mt-1 text-sm text-slate-600">
            بعد إنشاء المفتاح، استبدل{" "}
            <code className="rounded bg-slate-100 px-1 text-xs">alb_...</code> في
            الملف أدناه.
          </p>
          <pre
            dir="ltr"
            className="mt-3 overflow-x-auto rounded-lg border border-[var(--journal-border)] bg-slate-950 p-4 text-start text-xs leading-6 text-emerald-100"
          >
            {CURSOR_MCP_EXAMPLE}
          </pre>
        </section>
      </main>
    </div>
  );
}
