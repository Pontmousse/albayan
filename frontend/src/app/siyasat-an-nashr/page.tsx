import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "سياسة النشر | البيان",
  description: "سياسة نشر خفيفة لمجلة البيان — نسخة أولية قابلة للتوسع إن شاء الله.",
};

export default function PublishingPolicyPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          سياسة النشر
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          نسخة مختصرة للتوجيه العام — التفاصيل الكاملة ستُضاف لاحقًا إن شاء الله.
        </p>

        <div className="mt-8 space-y-8 text-slate-800">
          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">الرسالة</h2>
            <p className="mt-2 text-sm leading-7">
              تسعى «البيان» إلى نشر بحث علمي رصين بالعربية، يراعي التوحيد والنزاهة
              الأكاديمية، ويخدم المعرفة دون فصل بين العلوم التطبيقية وبين التدبر في
              آيات الله وخلقه.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">النطاق</h2>
            <p className="mt-2 text-sm leading-7">
              تُقبل مساهمات في مجالات العلوم والهندسة والتقنية والدراسات ذات الصلة،
              بشرط الالتزام بمعايير الجودة والتحكيم. تحديد التخصصات الدقيقة سيُوسَّع
              لاحقًا إن شاء الله.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">التحكيم</h2>
            <p className="mt-2 text-sm leading-7">
              تُطبَّق سياسة التحكيم الأقران (محايد). هوية المحكمين سرّية في المرحلة
              الافتراضية، ويُفضَّل الإفصاح عند النشر المفتوح للتحكيم حسب ما يُقرّ
              لاحقًا إن شاء الله.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">النزاهة والأخلاقيات</h2>
            <ul className="mt-2 list-inside list-disc space-y-2 text-sm leading-7">
              <li>رفض الانتحال وتزييف البيانات.</li>
              <li>إعلان تضارب المصالح عند الاقتضاء.</li>
              <li>الالتزام بحقوق المشاركين في البحث والمؤسسات.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">النشر والوصول</h2>
            <p className="mt-2 text-sm leading-7">
              تتجه المجلة إلى نموذج وصول حر (مفتوح) قدر الإمكان. النشر{" "}
              <strong>مجاني</strong> للمؤلفين في هذه المرحلة. تفاصيل الترخيص (مثل
              Creative Commons) ستُعلَن عند اكتمال الإطار القانوني إن شاء الله.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[var(--journal-accent)]">السحب والتصحيح</h2>
            <p className="mt-2 text-sm leading-7">
              يُعالَج طلب سحب المخطوطة أو نشر تصحيح وفق إجراءات تُوضَّح لاحقًا، مع
              مراعاة حق القارئ والمجتمع العلمي.
            </p>
          </section>

          <p className="rounded-lg border border-amber-200 bg-white/70 p-4 text-sm text-slate-700">
            لطلبات استثناء أو أسئلة حول السياسة، راجع صفحة{" "}
            <Link href="/al-tawasul" className="font-semibold text-[var(--journal-accent)] hover:underline">
              التواصل
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
