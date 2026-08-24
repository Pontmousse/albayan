/** مسار صفحة الشروح التعليمية — slug عربي متسق مع الصفحات العامة. */
export const TUTORIALS_HREF = "/al-durus";

/** تسمية الواجهة العامة — لا تُستعمل «فيديوهات تعليمية». */
export const TUTORIALS_LABEL = "دروس تعليمية";

export type TutorialLesson = {
  id: string;
  title: string;
  description: string;
  /** مسار ملف تحت `public/` إن وُجد؛ وإلا تُعرض لوحة انتظار التسجيل. */
  src: string | null;
};

const FEMININE_ORDINALS = [
  "الأولى",
  "الثانية",
  "الثالثة",
  "الرابعة",
  "الخامسة",
  "السادسة",
  "السابعة",
  "الثامنة",
  "التاسعة",
  "العاشرة",
] as const;

const EASTERN_DIGITS = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"] as const;

export function toEasternNumeral(value: number): string {
  return String(value).replace(/\d/g, (digit) => EASTERN_DIGITS[Number(digit)] ?? digit);
}

export function tutorialEpisodeLabel(index: number): string {
  const ordinal = FEMININE_ORDINALS[index];
  return ordinal ? `الحلقة ${ordinal}` : `الحلقة ${toEasternNumeral(index + 1)}`;
}

/**
 * حلقات المرحلة الأولى المعروضة الآن.
 * البقية (الحفظ والتقديم، المعادلات، الصور، متابعة التحكيم، المراجعة، الإعدادات)
 * تُضاف عند توفر التسجيل — انظر `docs/afkar-al-mashrou.md` القسم ٣.
 */
export const tutorialLessons: TutorialLesson[] = [
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
