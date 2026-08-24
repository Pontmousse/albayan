import type { Metadata } from "next";
import Link from "next/link";
import { LessonsFolio } from "@/components/journal/lessons-folio";
import { TUTORIALS_LABEL, tutorialLessons } from "@/lib/tutorials";

export const metadata: Metadata = {
  title: `${TUTORIALS_LABEL} | البيان`,
  description:
    "دروس قصيرة تعرّف الباحث بمنصة مجلة البيان: الحساب، مكتبي، وكتابة المخطوطة.",
};

export default function TutorialsPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <nav aria-label="مسار الصفحة" className="text-xs text-slate-500">
          <ol className="flex flex-wrap items-center gap-1.5">
            <li>
              <Link
                href="/"
                className="transition hover:text-[var(--journal-accent)]"
              >
                الرئيسية
              </Link>
            </li>
            <li aria-hidden className="text-slate-400">
              /
            </li>
            <li>
              <span className="font-medium text-slate-700">{TUTORIALS_LABEL}</span>
            </li>
          </ol>
        </nav>

        <p className="mt-5 text-xs font-semibold text-[var(--journal-accent)]">
          للمؤلفين والمراجعين
        </p>
        <h1
          className="mt-2 text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          {TUTORIALS_LABEL}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-8 text-slate-600 sm:text-base">
          شروح وجيزة تُعين الباحث على معرفة منصة «البيان»: من إنشاء الحساب إلى
          الشروع في المخطوطة من «مكتبي». نبدأ بحلقتين، ونُلحق بهما بقية الشروح
          تباعًا إن شاء الله.
        </p>

        <LessonsFolio lessons={tutorialLessons} />

        <p className="mt-10 max-w-3xl rounded-xl border border-[var(--journal-border)] bg-white/70 p-4 text-sm leading-7 text-slate-700">
          للتقديم بعد المشاهدة، راجع{" "}
          <Link
            href="/irshadat-al-mualifin"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            إرشادات المؤلفين
          </Link>
          {" و"}
          <Link
            href="/siyasat-an-nashr"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            سياسة النشر
          </Link>
          {". إن كان لك حساب، فباب العمل هو "}
          <Link
            href="/maktabi"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            مكتبي
          </Link>
          {"."}
        </p>
      </main>
    </div>
  );
}
