import { describe, expect, it } from "vitest";

import { butexDigitFormForNumeralSystem } from "@/lib/butex-numerals";

describe("butexDigitFormForNumeralSystem", () => {
  it("maps Al-Bayan Arabic numerals to BuTeX Arabic-Indic presentation", () => {
    expect(butexDigitFormForNumeralSystem("arab")).toBe("arabicIndic");
  });

  it("maps Al-Bayan Western numerals to BuTeX Western presentation", () => {
    expect(butexDigitFormForNumeralSystem("latn")).toBe("western");
  });
});
