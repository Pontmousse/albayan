import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "إرشادات المؤلفين | البيان",
  description: "دليل خفيف لإعداد المخطوطات لمجلة البيان — نسخة أولية.",
};

export default function AuthorGuidelinesPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          إرشادات المؤلفين
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          خطوات عملية مختصرة — النماذج والقوالب التفصيلية ستُرفَع لاحقًا إن شاء الله.
        </p>

        <div className="mt-8 space-y-8 text-slate-800">
          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">قبل الإرسال</h2>
            <ul className="mt-2 list-inside list-disc space-y-2 text-sm leading-7">
              <li>التأكد من أصالة الفكرة وعدم تكرار النشر في مكان آخر.</li>
              <li>إعداد قائمة مراجع أولية ومصادر البيانات إن وُجدت.</li>
              <li>مراجعة سياسة النشر في صفحة «سياسة النشر».</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">هيكل المقال المقترح</h2>
            <ol className="mt-2 list-inside list-decimal space-y-2 text-sm leading-7">
              <li>العنوان والمؤلفون والانتماء المؤسسي.</li>
              <li>الملخص العربي (والإنجليزي لاحقًا إن شاء الله عند الحاجة).</li>
              <li>الكلمات المفتاحية.</li>
              <li>المقدمة والمنهجية والنتائج والمناقشة والخاتمة.</li>
              <li>المراجع والملحقات.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">الصياغة واللغة</h2>
            <p className="mt-2 text-sm leading-7">
              العربية الفصحى البليغة المفهومة للتخصص؛ تجنّب الإطالة غير الضرورية.
              المصطلحات الأجنبية يُستحسن توضيحها عند أول ورود.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">الجداول والأشكال</h2>
            <p className="mt-2 text-sm leading-7">
              جودة عالية للأشكال، وتسميات واضحة للجداول. صيغ الملفات المقبولة
              (مثل PDF أو PNG) ستُحدَّد في دليل التنسيق لاحقًا إن شاء الله.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">المراجع</h2>
            <p className="mt-2 text-sm leading-7">
              اعتماد أسلوب مرجعي موحّد (مثل APA أو IEEE أو أسلوب عربي مخصص) سيُعلَن
              عند اعتماد دليل التنسيق النهائي إن شاء الله. إلى ذلك الحين، يُفضَّل
              الاتساق داخل المخطوطة الواحدة.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">التقديم</h2>
            <p className="mt-2 text-sm leading-7">
              بوابة الرفع والتتبع ستُفعَّل لاحقًا إن شاء الله. مؤقتًا يمكن التواصل
              عبر قناة التواصل عندما تكون جاهزة.
            </p>
          </section>

          <p className="rounded-lg border border-[var(--journal-border)] bg-white/70 p-4 text-sm text-slate-700">
            للاطلاع على الإطار العام للمجلة:{" "}
            <Link href="/siyasat-an-nashr" className="font-semibold text-[var(--journal-accent)] hover:underline">
              سياسة النشر
            </Link>
            .
          </p>
        </div>
      </main>
    </div>
  );
}
