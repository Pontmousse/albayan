import Link from "next/link";
import { SearchPanel } from "@/components/search-panel";

const articles = [
  {
    id: "1",
    type: "بحث أصلي",
    title: "نمذجة انتشار المعرفة في المجلات العلمية العربية الرقمية",
    authors: "د. سارة المهدي، د. يوسف النجار",
    abstract:
      "تقدّم الدراسة إطارًا كميًا لتقييم انتشار الاستشهادات عبر المنصات المفتوحة، مع مقارنة بين مؤشرات الظهور والتأثير في بيئات نشر مختلفة.",
    date: "٢٤ ذو القعدة ١٤٤٧ هـ",
    isoDate: "2026-05-12",
  },
  {
    id: "2",
    type: "مراجعة شاملة",
    title: "التحكيم الأقران والشفافية: دروس من ممارسات النشر المفتوح العالمية",
    authors: "د. هدى الكردي",
    abstract:
      "مراجعة منهجية للأدبيات الحديثة حول نماذج التحكيم المفتوح، والتحديات المرتبطة بالهوية والجودة في المجلات متعددة التخصصات.",
    date: "١٠ ذو القعدة ١٤٤٧ هـ",
    isoDate: "2026-04-28",
  },
  {
    id: "3",
    type: "ورقة منهجية",
    title: "معمارية بيانات وصفية موحّدة لأرشفة الأعداد الإلكترونية للمجلات العلمية",
    authors: "م. خالد الزهراني، د. لينا العتيبي",
    abstract:
      "اقتراح مخطط بيانات وصفية قابل للتوسع يسهّل الربط مع مستودعات المؤسسات وبوابات الفهرسة، مع أمثلة تطبيقية على أعداد تجريبية.",
    date: "٢٦ رمضان ١٤٤٧ هـ",
    isoDate: "2026-03-15",
  },
  {
    id: "4",
    type: "تعليق علمي",
    title: "حول معايير إتاحة البيانات البحثية في العلوم التجريبية",
    authors: "د. عمر الحسني",
    abstract:
      "نقاش موجز حول متطلبات إتاحة البيانات والتكرار، وعلاقتها بسياسات المجلات وحقوق المؤلفين في السياق العربي.",
    date: "١٩ شعبان ١٤٤٧ هـ",
    isoDate: "2026-02-07",
  },
];

const verses = [
  "أَلَمْ تَرَ أَنَّ اللَّهَ أَنْزَلَ مِنَ السَّمَاءِ مَاءً فَأَخْرَجْنَا بِهِ ثَمَرَاتٍ مُخْتَلِفًا أَلْوَانُهَا ۚ وَمِنَ الْجِبَالِ جُدَدٌ بِيضٌ وَحُمْرٌ مُخْتَلِفٌ أَلْوَانُهَا وَغَرَابِيبُ سُودٌ",
  "وَمِنَ النَّاسِ وَالدَّوَابِّ وَالْأَنْعَامِ مُخْتَلِفٌ أَلْوَانُهُ كَذَٰلِكَ ۗ إِنَّمَا يَخْشَى اللَّهَ مِنْ عِبَادِهِ الْعُلَمَاءُ ۗ إِنَّ اللَّهَ عَزِيزٌ غَفُورٌ",
  "إِنَّ الَّذِينَ يَتْلُونَ كِتَابَ اللَّهِ وَأَقَامُوا الصَّلَاةَ وَأَنْفَقُوا مِمَّا رَزَقْنَاهُمْ سِرًّا وَعَلَانِيَةً يَرْجُونَ تِجَارَةً لَنْ تَبُورَ",
  "لِيُوَفِّيَهُمْ أُجُورَهُمْ وَيَزِيدَهُمْ مِنْ فَضْلِهِ ۚ إِنَّهُ غَفُورٌ شَكُورٌ",
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-[var(--journal-border)] bg-[linear-gradient(135deg,var(--journal-paper)_0%,var(--journal-accent-soft)_45%,#e9f1ec_100%)]">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-emerald-800 via-amber-600 to-slate-900" />
          <div className="mx-auto max-w-7xl px-3 py-6 sm:px-5 sm:py-8 lg:px-8 lg:py-10">
            <div className="rounded-2xl border border-[var(--journal-border)] bg-white/70 p-4 shadow-sm backdrop-blur sm:rounded-[2rem] sm:p-7 lg:p-8">
              <div
                className="text-center text-lg leading-relaxed text-emerald-950 sm:text-3xl lg:text-4xl"
                style={{ fontFamily: "AlmaghribiWarch, var(--font-display-ar), serif" }}
              >
                أعوذ بالله من الشيطان الرجيم
                <br />
                بسم الله الرحمن الرحيم
              </div>
              <blockquote className="mt-4 text-pretty text-center text-base font-bold leading-[1.95] text-slate-950 sm:mt-6 sm:text-2xl sm:leading-[2.05] lg:text-3xl">
                {verses.map((verse, index) => (
                  <span key={verse}>
                    {verse}
                    {index < verses.length - 1 ? (
                      <span className="mx-1.5 inline-block text-[var(--journal-gold)] sm:mx-3">۞</span>
                    ) : null}
                  </span>
                ))}
              </blockquote>
              <p
                className="mt-3 text-center text-base font-bold text-[var(--journal-accent)] sm:mt-4 sm:text-xl"
                style={{ fontFamily: "var(--font-display-ar), serif" }}
              >
                سورة فاطر [٢٧، ٢٨، ٢٩، ٣٠]
              </p>
              <p className="mx-auto mt-4 max-w-4xl text-center text-sm leading-7 text-slate-700 sm:mt-5 sm:text-base">
                تنطلق «البيان» من أن عقيدة التوحيد والنظر في آيات الله في الكون لا
                ينفصلان عن البحث في العلوم التطبيقية؛ فالعلم الحق يزيد صاحبه خشية
                وبصيرة. ومع ذلك فإنّ غاية البحث عندنا تبدأ بالتعبد لله تعالى،
                والتعرّف على أسمائه وصفاته، والتدبّر والتفكّر في آياته وفي خلقه،
                ثمّ يتوسّع بعد ذلك ليشمل عمارة الأرض وخدمة الإنسان بما يرضي الله
                ويحقّق مقاصد الشريعة.
              </p>
            </div>
          </div>
        </section>

        <section className="border-b border-[var(--journal-border)] bg-[linear-gradient(180deg,var(--journal-accent-soft)_0%,var(--journal-paper)_100%)]">
          <div className="mx-auto grid max-w-7xl gap-8 px-3 py-8 sm:gap-10 sm:px-6 sm:py-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-center lg:px-8 lg:py-14">
            <div className="space-y-5 sm:space-y-6">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                العدد الحالي · وضع تجريبي
              </p>
              <h1
                className="text-balance text-2xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl"
                style={{ fontFamily: "var(--font-display-ar), serif" }}
              >
                منصة عربية للنشر العلمي الرصين والوصول الحر للمعرفة
              </h1>
              <p className="max-w-2xl text-pretty text-sm leading-relaxed text-slate-600 sm:text-lg">
                تهدف «البيان» إلى دعم الباحثين والمؤسسات الأكاديمية عبر تحكيم أقران صارم،
                وسياسات نشر واضحة، وأرشفة دائمة للأبحاث المعتمدة وفق أعلى المعايير
                الدولية في النزاهة العلمية.
              </p>
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
                <a
                  href="#"
                  className="inline-flex min-h-11 items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
                >
                  استعراض الأعداد
                </a>
                <Link
                  href="/irshadat-al-mualifin"
                  className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-[var(--journal-accent)] hover:bg-white"
                >
                  إرشادات المؤلفين
                </Link>
              </div>
            </div>
            <SearchPanel />
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-3 py-8 sm:px-6 sm:py-12 lg:px-8">
          <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2
                className="text-2xl font-bold text-slate-900"
                style={{ fontFamily: "var(--font-display-ar), serif" }}
              >
                أحدث المقالات المنشورة
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                عيّنة توضيحية من العدد الحالي — البيانات ثابتة في الواجهة إلى حين ربط قاعدة
                البيانات إن شاء الله.
              </p>
            </div>
            <a
              href="#"
              className="text-sm font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
            >
              عرض جميع المقالات
            </a>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {articles.map((article) => (
              <article
                key={article.id}
                className="flex flex-col rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm transition hover:border-[var(--journal-accent)] hover:bg-white hover:shadow-md"
              >
                <div className="mb-3 flex items-center justify-between gap-3 text-xs text-slate-500">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
                    {article.type}
                  </span>
                  <time dateTime={article.isoDate}>{article.date}</time>
                </div>
                <h3
                  className="text-lg font-bold leading-snug text-slate-900"
                  style={{ fontFamily: "var(--font-display-ar), serif" }}
                >
                  <a href="#" className="hover:text-[var(--journal-accent)]">
                    {article.title}
                  </a>
                </h3>
                <p className="mt-2 text-sm font-medium text-slate-700">{article.authors}</p>
                <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600">
                  {article.abstract}
                </p>
                <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4 text-xs text-slate-500">
                  <span>معرّف DOI · قيد الإسناد إن شاء الله</span>
                  <a
                    href="#"
                    className="font-semibold text-[var(--journal-accent)] hover:underline"
                  >
                    الملخص الكامل
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
