import type { Metadata } from "next";
import Link from "next/link";
import { McpClientCarousel } from "@/components/wukala/mcp-client-carousel";
import { WukalaCtaButton } from "@/components/wukala/wukala-cta-button";

export const metadata: Metadata = {
  title: "الوكلاء | البيان",
  description:
    "اربط وكيلك الذكي بمجلة البيان — Cursor أو ChatGPT أو Claude.",
};

export default function WukalaPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-14">
        <p className="text-xs font-semibold text-emerald-700">
          ربط الوكيل الذكي
        </p>
        <h1
          className="mt-3 text-balance text-3xl font-bold text-slate-900 sm:text-4xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          اربط وكيلك الذكي بمجلة البيان
        </h1>
        <p className="mt-4 text-pretty text-sm leading-7 text-slate-600 sm:text-base">
          اختر برنامجك (
          <strong className="font-semibold text-slate-800">Cursor</strong> أو{" "}
          <strong className="font-semibold text-slate-800">ChatGPT</strong> أو{" "}
          <strong className="font-semibold text-slate-800">Claude</strong>
          ) واتبع الخطوات. البرنامج يساعدك في الكتابة، وأنت تحفظ وتقدّم من
          منصة البيان.
        </p>

        <div className="mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <WukalaCtaButton className="w-full sm:w-auto" />
          <Link
            href="/irshadat-al-mualifin"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)]"
          >
            إرشادات المؤلفين
          </Link>
        </div>

        <McpClientCarousel />

        <section className="mt-10 rounded-2xl border border-[var(--journal-border)] bg-white/80 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">كيف يعمل الربط؟</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">
            الربط يعني أن برنامج الذكاء الاصطناعي يرى ملفك في المجلة بعد أن
            تسمح له. نسمّي هذه الصلة MCP. لا يقدّم المقال عنك ولا يتّخذ قرارات
            التحرير.
          </p>
        </section>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <section className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
            <h2 className="text-sm font-bold text-emerald-900">ما يفعله الوكيل</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-emerald-950/80">
              <li>قراءة ملفك ومقالاتك</li>
              <li>مساعدة في الكتابة (مسودة الجلسة — قريباً)</li>
              <li>مسودة ملاحظات المراجعة</li>
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
      </main>
    </div>
  );
}
