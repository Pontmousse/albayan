import type { NumeralSystem } from "@/lib/numerals";

export type AlbayanButexDigitForm = "western" | "arabicIndic";

export function butexDigitFormForNumeralSystem(
  numeralSystem: NumeralSystem,
): AlbayanButexDigitForm {
  return numeralSystem === "latn" ? "western" : "arabicIndic";
}
