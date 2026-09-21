import { describe, expect, it } from "vitest";

import {
  parseMappingTarget,
  serializeMappingTarget,
} from "@/lib/mapping-fonts";

describe("mapping font codec", () => {
  it("uses one plain default state and serializes special fonts canonically", () => {
    expect(serializeMappingTarget("السرعة", "default")).toBe("السرعة");
    expect(serializeMappingTarget("السرعة", "takween")).toBe(
      "\\butextakween{السرعة}",
    );
    expect(serializeMappingTarget("السرعة", "diwani")).toBe(
      "\\butexdiwani{السرعة}",
    );
    expect(serializeMappingTarget("السرعة", "diwaniOutline")).toBe(
      "\\butexdiwanioutline{السرعة}",
    );
    expect(serializeMappingTarget("السرعة", "maghribi")).toBe(
      "\\butexmaghribi{السرعة}",
    );
  });

  it("parses raw values as the default no-special-font state", () => {
    expect(parseMappingTarget("x_1")).toEqual({
      target: "x_1",
      fontId: "default",
    });
  });

  it("keeps older text-wrapped default values lossless until edited", () => {
    const oldDefault = "\\text{السرعة}";
    const parsed = parseMappingTarget(oldDefault);

    expect(parsed).toEqual({
      target: "السرعة",
      fontId: "default",
      legacySerialized: oldDefault,
    });
    expect(
      serializeMappingTarget(
        parsed.target,
        parsed.fontId,
        parsed.legacySerialized,
      ),
    ).toBe(oldDefault);
    expect(serializeMappingTarget(parsed.target, parsed.fontId)).toBe("السرعة");
  });

  it("round-trips every current style, including nested braces", () => {
    for (const fontId of [
      "default",
      "takween",
      "diwani",
      "diwaniOutline",
      "maghribi",
    ] as const) {
      const serialized = serializeMappingTarget("ق_{1_{2}}", fontId);
      const parsed = parseMappingTarget(serialized);
      expect(parsed.target).toBe("ق_{1_{2}}");
      expect(parsed.fontId).toBe(fontId);
    }
  });

  it("keeps the old Jissr-style Diwani aliases readable", () => {
    expect(parseMappingTarget("\\text{\\diwani{السرعة}}")).toEqual({
      target: "السرعة",
      fontId: "diwani",
    });
    expect(parseMappingTarget("\\diwani{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "diwani",
    });
  });

  it("preserves escaped braces inside supported wrappers", () => {
    expect(parseMappingTarget("\\butexdiwani{أ\\{ب\\}ج}")).toEqual({
      target: "أ\\{ب\\}ج",
      fontId: "diwani",
    });
  });

  it("preserves unknown wrappers losslessly", () => {
    const legacy = "  \\text{\\legacyfont{السرعة}}  ";
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
