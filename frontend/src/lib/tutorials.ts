/** مسار صفحة الشروح التعليمية — slug عربي متسق مع الصفحات العامة. */
export const TUTORIALS_HREF = "/al-durus";

export type TutorialVideo = {
  id: string;
  title: string;
  description: string;
  /** مسار ملف تحت `public/` إن وُجد؛ وإلا تُعرض بطاقة «قريبًا». */
  src: string | null;
};

/**
 * حلقات المرحلة الأولى المعروضة الآن.
 * البقية (الحفظ والتقديم، المعادلات، الصور، متابعة التحكيم، المراجعة، الإعدادات)
 * تُضاف عند توفر التسجيل — انظر `docs/afkar-al-mashrou.md` القسم ٣.
 */
export const tutorialVideos: TutorialVideo[] = [
  {
    id: "al-bidaya-hisab-wawajha",
    title: "البدء: الحساب والواجهة",
    description:
      "تُعرّف هذه الحلقة الباحث بمنصة المجلة: كيف يُنشئ حسابه، وكيف يدخل إليها، ثم أين يجد أبوابها و«مكتبي» الذي تُدار منه المقالات.",
    src: null,
  },
  {
    id: "maktabi-maqal-jadid",
    title: "مكتبي: مقال جديد",
    description:
      "تُبيّن كيف يبدأ المؤلف مقالًا من «مكتبي»: يضع عنوانه وملخّصه إن شاء، ثم ينتقل إلى المحرر ليكتب مخطوطته.",
    src: null,
  },
];
