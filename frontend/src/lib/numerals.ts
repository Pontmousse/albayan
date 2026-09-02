export type NumeralSystem = "arab" | "latn";

export const DEFAULT_NUMERAL_SYSTEM: NumeralSystem = "arab";
export const NUMERAL_STORAGE_KEY = "albayan:numeral-system";

const ARAB_DIGITS = "٠١٢٣٤٥٦٧٨٩";
const ASCII_DIGITS = "0123456789";

export function isNumeralSystem(value: unknown): value is NumeralSystem {
  return value === "arab" || value === "latn";
}

/** يحوّل الأرقام العربية المشرقية والفارسية إلى ASCII عند حدود الإدخال. */
export function normalizeDigits(value: string): string {
  return value
    .replace(/[٠-٩]/g, (digit) => String(digit.charCodeAt(0) - 0x0660))
    .replace(/[۰-۹]/g, (digit) => String(digit.charCodeAt(0) - 0x06f0));
}

/** يطبّع حقلًا رقميًا، ويعيد null بدل إسقاط المحارف غير الرقمية بصمت. */
export function normalizeNumericInput(
  value: string,
  maxLength?: number,
): string | null {
  const normalized = normalizeDigits(value.trim());
  if (!/^\d*$/.test(normalized)) return null;
  if (maxLength !== undefined && normalized.length > maxLength) return null;
  return normalized;
}

export function parseBoundedInteger(
  value: string,
  min: number,
  max: number,
): number | null {
  if (!/^\d+$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= min && parsed <= max
    ? parsed
    : null;
}

/** يغيّر المحارف الرقمية فقط داخل نص يملكه التطبيق، من دون المساس بعلاماته. */
export function formatDigits(value: string | number, system: NumeralSystem): string {
  const normalized = normalizeDigits(String(value));
  if (system === "latn") return normalized;
  return normalized.replace(/[0-9]/g, (digit) => ARAB_DIGITS[Number(digit)] ?? digit);
}

export function formatNumber(
  value: number | bigint,
  system: NumeralSystem,
  options?: Intl.NumberFormatOptions,
): string {
  return new Intl.NumberFormat(`ar-SA-u-nu-${system}`, options).format(value);
}

export function numeralSample(system: NumeralSystem): string {
  return system === "arab" ? formatDigits(123, system) : ASCII_DIGITS.slice(1, 4);
}
