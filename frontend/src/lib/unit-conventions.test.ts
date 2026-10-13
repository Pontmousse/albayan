import { describe, expect, it } from "vitest";
import { validateUnitConventions, validateUnitDisplay } from "./unit-conventions";

describe("unit conventions", () => {
  it("accepts safe Arabic multiword display and punctuation", () => {
    expect(validateUnitDisplay("وحدة معايرة")).toBe("وحدة معايرة");
    expect(validateUnitDisplay("و.م")).toBe("و.م");
  });
  it.each(["", "a/b", "a_b", "a  b", " كغ", "كغ ", "\\input{evil}", "."])(
    "rejects unsafe displays %s", (text) => {
      expect(() => validateUnitDisplay(text)).toThrow();
    }
  );
  it("keeps canonical case and custom identity separate", () => {
    const result = validateUnitConventions(
      { overrides: { kg: "كغ" }, custom_units: { CU: { display: "وحدة معايرة" } } },
      ["kg", "m"], ["kg", "CU"],
    );
    expect(result.custom_units.CU.display).toBe("وحدة معايرة");
    expect(result.overrides.kg).toBe("كغ");
  });
  it("blocks custom identities shadowing registry tokens", () => {
    expect(() => validateUnitConventions(
      { overrides: {}, custom_units: { kg: { display: "بديل" } } },
      ["kg"], ["kg"],
    )).toThrow();
  });
  it("rejects malformed canonical identifiers", () => {
    expect(() => validateUnitConventions(
      { overrides: {}, custom_units: { "a_b": { display: "مخصص" } } },
      [], [],
    )).toThrow();
  });
});
