import { UserFacingError } from "@/lib/user-facing-errors";
import type { UnitConventions } from "@/lib/api/units";

export const UNIT_TOKEN_PATTERN = /^[A-Za-z][A-Za-z0-9]*$/u;
const ALLOWED_PUNCTUATION = new Set([".", "·", "-", "٫"]);

export function validateUnitDisplay(value: string): string {
  if (!value || value.length > 64 || value !== value.trim() || value.includes("  ")) {
    throw new UserFacingError("يجب أن تتألف كتابة الوحدة من ١ إلى ٦٤ محرفاً دون مسافات زائدة.");
  }
  if (!Array.from(value).some((char) => /\p{L}/u.test(char))) {
    throw new UserFacingError("يجب أن تحتوي كتابة الوحدة على حرف واحد على الأقل.");
  }
  for (const char of value) {
    if (
      char === " " || ALLOWED_PUNCTUATION.has(char) ||
      /[\p{L}\p{M}\p{N}]/u.test(char)
    ) continue;
    throw new UserFacingError("تقبل الوحدات نصاً عادياً فقط، دون أوامر LaTeX أو رموز خاصة.");
  }
  return value;
}

export function validateUnitConventions(
  data: UnitConventions,
  registered: readonly string[],
  usedTokens: readonly string[],
  previous?: UnitConventions,
): UnitConventions {
  if (
    Object.keys(data.overrides).length > 256 ||
    Object.keys(data.custom_units).length > 256
  ) throw new UserFacingError("تجاوزت اصطلاحات الوحدات الحد المسموح.");

  const registry = new Set(registered);
  const used = new Set(usedTokens);
  for (const [token, display] of Object.entries(data.overrides)) {
    if (!registry.has(token)) {
      throw new UserFacingError(`الوحدة «${token}» غير موجودة في سجل الوحدات.`);
    }
    validateUnitDisplay(display);
  }
  for (const [token, definition] of Object.entries(data.custom_units)) {
    if (!UNIT_TOKEN_PATTERN.test(token)) {
      throw new UserFacingError("رمز الوحدة المخصصة يجب أن يبدأ بحرف لاتيني ويتكون من حروف وأرقام فقط.");
    }
    if (registry.has(token) || token in data.overrides) {
      throw new UserFacingError(`لا يمكن إعادة تعريف الوحدة المسجلة «${token}».`);
    }
    if (definition.name !== undefined &&
        (!definition.name.trim() || definition.name !== definition.name.trim() ||
         definition.name.length > 100)) {
      throw new UserFacingError("اسم الوحدة يجب أن يكون غير فارغ وبحد أقصى ١٠٠ محرف.");
    }
    validateUnitDisplay(definition.display);
  }
  for (const token of Object.keys(previous?.custom_units ?? {})) {
    if (used.has(token) && !(token in data.custom_units)) {
      throw new UserFacingError(`لا يمكن حذف «${token}» لأنها مستخدمة في المعادلات.`);
    }
  }
  return {
    overrides: { ...data.overrides },
    custom_units: Object.fromEntries(
      Object.entries(data.custom_units).map(([key, value]) => [key, { ...value }])
    ),
  };
}
