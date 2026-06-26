import type { Metadata } from "next";
import Link from "next/link";
import { contactEmail } from "@/lib/nav-config";

export const metadata: Metadata = {
  title: "التواصل | البيان",
  description: "قنوات التواصل مع مجلة البيان.",
};

export default function ContactPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          التواصل
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          للاستفسارات العامة، تقديم المقالات، أو الدعم الفني — راسلنا عبر البريد
          الإلكتروني.
        </p>

        <div className="mt-10 rounded-2xl border border-amber-200/80 bg-white/80 p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">البريد الإلكتروني</p>
          <a
            href={`mailto:${contactEmail}`}
            className="mt-2 inline-block text-xl font-semibold text-[var(--journal-accent)] transition-colors duration-200 hover:text-[var(--journal-accent-strong)]"
          >
            {contactEmail}
          </a>
          <p className="mt-4 text-sm leading-7 text-slate-600">
            نسعى للرد خلال أيام العمل. للمسائل المتعلقة بحسابك، يمكنك أيضًا مراجعة{" "}
            <Link
              href="/al-idayat"
              className="font-medium text-[var(--journal-accent)] underline-offset-2 hover:underline"
            >
              إعدادات الحساب
            </Link>{" "}
            بعد تسجيل الدخول.
          </p>
        </div>
      </main>
    </div>
  );
}
