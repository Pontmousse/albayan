import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "هيئة التحرير | البيان",
  description: "أعضاء هيئة التحرير في مجلة البيان — نسخة أولية للعرض.",
};

const editors = [
  {
    name: "د. أحمد الفلاح",
    role: "رئيس التحرير",
    affiliation: "قسم علوم الحاسوب — جامعة الأمثلة",
  },
  {
    name: "د. فاطمة الزهراني",
    role: "عضو هيئة التحرير",
    affiliation: "معهد الدراسات الإسلامية والعلوم التطبيقية",
  },
];

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
          أسماء توضيحية للعرض — ستُستكمل القائمة الرسمية لاحقًا إن شاء الله.
        </p>

        <ul className="mt-10 space-y-4">
          {editors.map((editor) => (
            <li
              key={editor.name}
              className="rounded-2xl border border-amber-200/80 bg-white/80 p-5 shadow-sm transition-shadow duration-200 hover:shadow-md"
            >
              <p className="text-lg font-bold text-slate-900">{editor.name}</p>
              <p className="mt-1 text-sm font-medium text-[var(--journal-accent)]">
                {editor.role}
              </p>
              <p className="mt-2 text-sm text-slate-600">{editor.affiliation}</p>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
