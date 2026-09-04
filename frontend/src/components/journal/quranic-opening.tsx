"use client";

import Image from "next/image";
import { useNumerals } from "@/components/numeral-provider";

const verses = [
  "أَلَمْ تَرَ أَنَّ اللَّهَ أَنْزَلَ مِنَ السَّمَاءِ مَاءً فَأَخْرَجْنَا بِهِ ثَمَرَاتٍ مُخْتَلِفًا أَلْوَانُهَا ۚ وَمِنَ الْجِبَالِ جُدَدٌ بِيضٌ وَحُمْرٌ مُخْتَلِفٌ أَلْوَانُهَا وَغَرَابِيبُ سُودٌ",
  "وَمِنَ النَّاسِ وَالدَّوَابِّ وَالْأَنْعَامِ مُخْتَلِفٌ أَلْوَانُهُ كَذَٰلِكَ ۗ إِنَّمَا يَخْشَى اللَّهَ مِنْ عِبَادِهِ الْعُلَمَاءُ ۗ إِنَّ اللَّهَ عَزِيزٌ غَفُورٌ",
  "إِنَّ الَّذِينَ يَتْلُونَ كِتَابَ اللَّهِ وَأَقَامُوا الصَّلَاةَ وَأَنْفَقُوا مِمَّا رَزَقْنَاهُمْ سِرًّا وَعَلَانِيَةً يَرْجُونَ تِجَارَةً لَنْ تَبُورَ",
  "لِيُوَفِّيَهُمْ أُجُورَهُمْ وَيَزِيدَهُمْ مِنْ فَضْلِهِ ۚ إِنَّهُ غَفُورٌ شَكُورٌ",
];

/** افتتاحية قرآنية + فلسفة المشروع — تُعرض في كلتا واجهتي الرئيسية. */
export function QuranicOpening() {
  const { formatNumber } = useNumerals();
  const verseNumbers = [27, 28, 29, 30]
    .map((number) => formatNumber(number))
    .join("، ");

  return (
    <section className="relative overflow-hidden border-b border-[var(--journal-border)] bg-[linear-gradient(135deg,var(--journal-paper)_0%,var(--journal-accent-soft)_45%,#e9f1ec_100%)]">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-emerald-800 via-amber-600 to-slate-900" />
      <div className="mx-auto max-w-7xl px-3 py-6 sm:px-5 sm:py-8 lg:px-8 lg:py-10">
        <div className="rounded-2xl border border-[var(--journal-border)] bg-white/70 p-4 shadow-sm backdrop-blur sm:rounded-[2rem] sm:p-7 lg:p-8">
          <div className="mb-4 flex justify-center sm:mb-5">
            <Image
              src="/official-logo.png"
              alt="شعار مجلة البيان"
              width={112}
              height={112}
              priority
              className="h-20 w-20 object-contain drop-shadow-[0_12px_22px_rgba(18,63,51,0.18)] sm:h-24 sm:w-24"
            />
          </div>
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
            سورة فاطر [{verseNumbers}]
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
  );
}
