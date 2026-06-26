import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "السياسات والشروط | البيان",
  description:
    "سياسة الأخلاقيات، سياسة الخصوصية، وشروط الاستخدام لمنصة مجلة البيان.",
};

export default function PoliciesAndTermsPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          السياسات والشروط
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          وثيقة موحّدة تجمع الأخلاقيات والخصوصية وشروط الاستخدام — نسخة أولية قابلة
          للتوسع إن شاء الله.
        </p>

        <div className="mt-10 space-y-12 text-slate-800">
          <section id="ethics">
            <h2 className="text-xl font-bold text-[var(--journal-accent)]">
              سياسة الأخلاقيات
            </h2>
            <div className="mt-4 space-y-3 text-sm leading-7">
              <p>
                تلتزم «البيان» بمعايير النزاهة العلمية: عدم الانتحال، الإفصاح عن تضارب
                المصالح، والتحقق من أصالة البحث قبل النشر.
              </p>
              <p>
                يُتوقَّع من المؤلفين والمراجعين الحفاظ على سرية المخطوطات وعدم إساءة
                استخدام المعلومات الواردة فيها.
              </p>
              <p>
                تُعالَج البلاغات عن سوء السلوك العلمي بجدية، وفق إجراءات توضَّح لاحقًا
                إن شاء الله.
              </p>
            </div>
          </section>

          <section id="privacy">
            <h2 className="text-xl font-bold text-[var(--journal-accent)]">
              سياسة الخصوصية
            </h2>
            <div className="mt-4 space-y-3 text-sm leading-7">
              <p>
                نجمع البيانات الضرورية لتشغيل المنصة — مثل البريد الإلكتروني والاسم عند
                التسجيل — عبر مزوّد المصادقة (Clerk) وقاعدة البيانات الخاصة بالمجلة.
              </p>
              <p>
                لا نبيع بيانات المستخدمين لأطراف ثالثة. تُستخدم المعلومات لإدارة
                الحسابات، سير المقالات، والتواصل المتعلق بالنشر العلمي.
              </p>
              <p>
                يمكنك طلب تحديث بياناتك أو حذف حسابك عبر التواصل معنا؛ التفاصيل
                التشغيلية ستُكمَّل مع توسّع المنصة إن شاء الله.
              </p>
            </div>
          </section>

          <section id="terms">
            <h2 className="text-xl font-bold text-[var(--journal-accent)]">
              شروط الاستخدام
            </h2>
            <div className="mt-4 space-y-3 text-sm leading-7">
              <p>
                باستخدامك منصة «البيان» فإنك توافق على الالتزام بهذه الشروط والسياسات
                المذكورة أعلاه.
              </p>
              <p>
                المحتوى المنشور يخضع لترخيص وصول حر قدر الإمكان؛ التفاصيل القانونية
                الدقيقة (مثل Creative Commons) ستُعلَن عند اكتمال الإطار إن شاء الله.
              </p>
              <p>
                النشر في المجلة <strong>مجاني</strong> — لا رسوم على المؤلفين في هذه
                المرحلة.
              </p>
              <p>
                نحتفظ بحق تعديل هذه الشروط مع إشعار معقول عبر المنصة عند الحاجة.
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
