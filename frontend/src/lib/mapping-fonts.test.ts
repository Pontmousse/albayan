import { describe, expect, it } from "vitest";

import {
  MAPPING_FONTS,
  mappingFontLabel,
  parseMappingTarget,
  serializeMappingTarget,
} from "@/lib/mapping-fonts";

describe("mapping font codec", () => {
  it("labels default and raw modes distinctly for authors", () => {
    expect(mappingFontLabel("default")).toBe("الافتراضي — نص عربي");
    expect(mappingFontLabel("none")).toBe("كما كُتبت (متقدم)");
    expect(mappingFontLabel("custom")).toBe("تنسيق محفوظ");
    expect(MAPPING_FONTS.find((font) => font.id === "none")?.mode).toBe(
      "raw",
    );
  });

  it("serializes all supported BuTeX mapping styles canonically", () => {
    expect(serializeMappingTarget("السرعة", "default")).toBe(
      "\\text{السرعة}",
    );
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
    expect(serializeMappingTarget("x_1", "none")).toBe("x_1");
  });

  it("parses canonical BuTeX wrappers into plain author-facing values", () => {
    expect(parseMappingTarget("\\text{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "default",
    });
    expect(parseMappingTarget("\\butextakween{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "takween",
    });
    expect(parseMappingTarget("\\butexdiwani{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "diwani",
    });
    expect(parseMappingTarget("\\butexdiwanioutline{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "diwaniOutline",
    });
    expect(parseMappingTarget("\\butexmaghribi{السرعة}")).toEqual({
      target: "السرعة",
      fontId: "maghribi",
    });
    expect(parseMappingTarget("x_1")).toEqual({
      target: "x_1",
      fontId: "none",
    });
  });

  it("round-trips supported styles, including nested braces", () => {
    for (const fontId of [
      "default",
      "takween",
      "diwani",
      "diwaniOutline",
      "maghribi",
      "none",
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
