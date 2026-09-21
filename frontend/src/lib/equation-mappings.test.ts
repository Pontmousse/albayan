import { describe, expect, it } from "vitest";

import {
  equationMappingRows,
  equationMappingsFromRows,
} from "@/lib/equation-mappings";

describe("equation mapping form helpers", () => {
  it("loads raw, canonical, and legacy wrapped mappings into editable rows", () => {
    expect(
      equationMappingRows({
        x: "س",
        y: "\\text{ص}",
        z: "\\butexdiwani{ع}",
        t: "\\butextakween{ق}",
        o: "\\butexdiwanioutline{ف}",
        m: "\\butexmaghribi{م}",
        legacy: "\\text{\\diwani{د}}",
      }),
    ).toEqual([
      { english: "x", arabic: "س", fontId: "none" },
      { english: "y", arabic: "ص", fontId: "default" },
      { english: "z", arabic: "ع", fontId: "diwani" },
      { english: "t", arabic: "ق", fontId: "takween" },
      { english: "o", arabic: "ف", fontId: "diwaniOutline" },
      { english: "m", arabic: "م", fontId: "maghribi" },
      { english: "legacy", arabic: "د", fontId: "diwani" },
    ]);
  });

  it("serializes plain author input according to the selected font", () => {
    expect(
      equationMappingsFromRows([
        { english: " x ", arabic: " س ", fontId: "default" },
        { english: "t", arabic: "ق", fontId: "takween" },
        { english: "y", arabic: "ص", fontId: "diwani" },
        { english: "o", arabic: "ف", fontId: "diwaniOutline" },
        { english: "m", arabic: "م", fontId: "maghribi" },
        { english: "z", arabic: "ع", fontId: "none" },
      ]),
    ).toEqual({
      x: "\\text{س}",
      t: "\\butextakween{ق}",
      y: "\\butexdiwani{ص}",
      o: "\\butexdiwanioutline{ف}",
      m: "\\butexmaghribi{م}",
      z: "ع",
    });
  });

  it("allows reset to an empty mapping dictionary", () => {
    expect(equationMappingsFromRows([])).toEqual({});
    expect(
      equationMappingsFromRows([
        { english: "", arabic: "", fontId: "default" },
      ]),
    ).toEqual({});
  });

  it("rejects partial and duplicate rows", () => {
    expect(() =>
      equationMappingsFromRows([
        { english: "x", arabic: "", fontId: "default" },
      ]),
    ).toThrow(/أكمل/);
    expect(() =>
      equationMappingsFromRows([
        { english: "x", arabic: "س", fontId: "default" },
        { english: " x ", arabic: "ص", fontId: "default" },
      ]),
    ).toThrow(/مكرر/);
  });

  it("preserves unknown legacy wrappers when saving unrelated edits", () => {
    const legacy = "\\text{\\legacyfont{س}}";
    const [row] = equationMappingRows({ x: legacy });

    expect(equationMappingsFromRows([row])).toEqual({ x: legacy });
  });
});
