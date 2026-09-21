import { describe, expect, it } from "vitest";

import {
  parseMappingTarget,
  serializeMappingTarget,
} from "@/lib/mapping-fonts";

describe("mapping font codec", () => {
  it("serializes supported mapping styles", () => {
    expect(serializeMappingTarget("السرعة", "default")).toBe(
      "\\text{السرعة}",
    );
    expect(serializeMappingTarget("السرعة", "diwani")).toBe(
      "\\text{\\diwani{السرعة}}",
    );
    expect(serializeMappingTarget("x_1", "none")).toBe("x_1");
  });

  it("parses supported wrappers into plain author-facing values", () => {
    expect(parseMappingTarget("\\text{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "default",
    });
    expect(parseMappingTarget("\\text{\\diwani{السرعة}}")).toEqual({
      target: "السرعة",
      fontId: "diwani",
    });
    expect(parseMappingTarget("x_1")).toEqual({
      target: "x_1",
      fontId: "none",
    });
  });

  it("round-trips supported styles", () => {
    for (const fontId of ["default", "diwani", "none"] as const) {
      const serialized = serializeMappingTarget("ق_{1}", fontId);
      const parsed = parseMappingTarget(serialized);
      expect(parsed.target).toBe("ق_{1}");
      expect(parsed.fontId).toBe(fontId);
    }
  });

  it("preserves unknown wrappers losslessly", () => {
    const legacy = "\\text{\\legacyfont{السرعة}}";
    const parsed = parseMappingTarget(legacy);

    expect(parsed).toEqual({
      target: legacy,
      fontId: "custom",
      legacySerialized: legacy,
    });
    expect(
      serializeMappingTarget(
        parsed.target,
        parsed.fontId,
        parsed.legacySerialized,
      ),
    ).toBe(legacy);
  });
});
