import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "هيئة التحرير | البيان",
  description: "أعضاء هيئة التحرير في مجلة البيان.",
};

export default function EditorialBoardPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          هيئة التحرير
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          القائمة الرسمية قيد الإعداد — لا نعرض أسماء وهمية.
        </p>

        <div className="mt-10 rounded-2xl border border-[var(--journal-border)] bg-white/80 p-6 text-center shadow-sm">
          <p className="text-sm leading-7 text-slate-600">
            ستُنشر أسماء هيئة التحرير هنا عند اعتمادها. للاستفسارات العامة، راجع{" "}
            <Link href="/al-tawasul" className="font-semibold text-[var(--journal-accent)] hover:underline">
              التواصل
            </Link>
            .
          </p>
        </div>
      </main>
    </div>
  );
}
