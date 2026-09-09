const MAX_PRODUCT_ERROR_LENGTH = 240;

const ARABIC_TEXT = /[\u0600-\u06ff]/u;
const ALLOWED_LATIN_PRODUCT_TERMS = /\b(?:JPEG|PNG|GIF|WebP)\b/g;
const TECHNICAL_IDENTIFIER = /(?:[A-Z][A-Z0-9]*_)+[A-Z0-9_]+/;
const TECHNICAL_LATIN_TEXT = /[A-Za-z]/;
const URL_OR_PATH = /(?:https?:\/\/|www\.|[/\\])/i;
const STACK_OR_SERIALIZED_DATA = /(?:\bat\s+\S+\s*\(|\{[\s\S]*\}|\[[\s\S]*\])/i;
const INTERNAL_ARABIC_TERMS =
  /(?:الخادم|قاعدة البيانات|التخزين|التجميع|جلسة التحرير|مستند الجلسة|طلب المستند|مفتاح الصورة|عامل\s+\S+|سجلّ?\s+(?:الأمر|الترجمة)|حمولة|استثناء|المكدس|نقطة النهاية|متغيّر? البيئة|غير مُهيّأ)/u;
const GENERIC_PRODUCT_ERRORS = new Set(["حدث خطأ أثناء الاتصال بالخادم."]);

/** يتحقق من أن النص العربي قصير ولا يحمل مؤشرات شائعة لتفاصيل تقنية داخلية. */
export function isSafeArabicProductMessage(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const message = value.trim();
  if (
    !message ||
    message.length > MAX_PRODUCT_ERROR_LENGTH ||
    !ARABIC_TEXT.test(message) ||
    /[\r\n\t]/u.test(message) ||
    URL_OR_PATH.test(message) ||
    STACK_OR_SERIALIZED_DATA.test(message) ||
    TECHNICAL_IDENTIFIER.test(message) ||
    INTERNAL_ARABIC_TERMS.test(message)
  ) {
    return false;
  }

  const withoutAllowedTerms = message.replace(ALLOWED_LATIN_PRODUCT_TERMS, "");
  return !TECHNICAL_LATIN_TEXT.test(withoutAllowedTerms);
}

/** خطأ محلي صيغت رسالته عمدًا للمستخدم، لا لغايات التشخيص. */
export class UserFacingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UserFacingError";
  }
}

/** لا يعرض رسالة الاستثناء إلا إذا كانت من نوع منتج موثوق واجتازت فحص السلامة. */
export function userFacingErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (
    error instanceof UserFacingError &&
    isSafeArabicProductMessage(error.message) &&
    !GENERIC_PRODUCT_ERRORS.has(error.message.trim())
  ) {
    return error.message.trim();
  }
  return fallback;
}
