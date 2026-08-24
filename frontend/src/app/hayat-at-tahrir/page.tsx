import type { Metadata } from "next";
import Link from "next/link";
import { editorialMembers } from "@/lib/editorial-board";

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
        <p className="mt-3 text-sm leading-8 text-slate-600 sm:text-base">
          تشرف هيئة التحرير على المسار العلمي للمجلة: توجيه المخطوطات، ورعاية
          التحكيم، واعتماد ما يصلح للنشر وفق معايير الرصانة والنزاهة.
        </p>

        <ul className="mt-10 space-y-5">
          {editorialMembers.map((member) => (
            <li key={`${member.role}-${member.name}`}>
              <article className="overflow-hidden rounded-2xl border border-[var(--journal-border)] bg-white/85 shadow-sm">
                <div className="h-1 bg-gradient-to-l from-emerald-800 via-amber-600 to-[var(--journal-accent)]" />
                <div className="px-6 py-6 sm:px-8 sm:py-7">
                  <p className="text-xs font-semibold tracking-wide text-[var(--journal-accent)]">
                    {member.role}
                  </p>
                  <h2
                    className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl"
                    style={{ fontFamily: "var(--font-display-ar), serif" }}
                  >
                    {member.name}
                  </h2>
                  <p className="mt-3 text-sm leading-8 text-slate-600 sm:text-[0.95rem]">
                    {member.affiliation}
                  </p>
                </div>
              </article>
            </li>
          ))}
        </ul>

        <p className="mt-8 text-sm leading-8 text-slate-600">
          يُعلن بقية أعضاء الهيئة عند اكتمال تشكيلها.
        </p>

        <p className="mt-8 rounded-xl border border-[var(--journal-border)] bg-white/70 p-4 text-sm leading-7 text-slate-700">
          للاستفسارات المتعلقة بالمجلة، يُرجى مراجعة صفحة{" "}
          <Link
            href="/al-tawasul"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            التواصل
          </Link>
          .
        </p>
      </main>
    </div>
  );
}
