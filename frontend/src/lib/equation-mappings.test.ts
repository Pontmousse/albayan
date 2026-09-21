import { describe, expect, it } from "vitest";

import {
  equationMappingRows,
  equationMappingsFromRows,
} from "@/lib/equation-mappings";

describe("equation mapping form helpers", () => {
  it("loads raw and wrapped mappings into editable rows", () => {
    expect(
      equationMappingRows({
        x: "س",
        y: "\\text{ص}",
        z: "\\text{\\diwani{ع}}",
      }),
    ).toEqual([
      { english: "x", arabic: "س", fontId: "none" },
      { english: "y", arabic: "ص", fontId: "default" },
      { english: "z", arabic: "ع", fontId: "diwani" },
    ]);
  });

  it("serializes plain author input according to the selected font", () => {
    expect(
      equationMappingsFromRows([
        { english: " x ", arabic: " س ", fontId: "default" },
        { english: "y", arabic: "ص", fontId: "diwani" },
        { english: "z", arabic: "ع", fontId: "none" },
      ]),
    ).toEqual({
      x: "\\text{س}",
      y: "\\text{\\diwani{ص}}",
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
