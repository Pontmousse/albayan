import { describe, expect, it } from "vitest";

import {
  equationMappingRows,
  equationMappingsFromRows,
} from "@/lib/equation-mappings";

describe("equation mapping form helpers", () => {
  it("loads existing mappings into editable rows", () => {
    expect(equationMappingRows({ x: "س", y: "ص" })).toEqual([
      { english: "x", arabic: "س" },
      { english: "y", arabic: "ص" },
    ]);
  });

  it("normalizes added and edited rows for persistence", () => {
    expect(
      equationMappingsFromRows([
        { english: " x ", arabic: " س " },
        { english: "y", arabic: "ص" },
      ]),
    ).toEqual({ x: "س", y: "ص" });
  });

  it("allows reset to an empty mapping dictionary", () => {
    expect(equationMappingsFromRows([])).toEqual({});
    expect(
      equationMappingsFromRows([{ english: "", arabic: "" }]),
    ).toEqual({});
  });

  it("rejects partial and duplicate rows", () => {
    expect(() =>
      equationMappingsFromRows([{ english: "x", arabic: "" }]),
    ).toThrow(/أكمل/);
    expect(() =>
      equationMappingsFromRows([
        { english: "x", arabic: "س" },
        { english: " x ", arabic: "ص" },
      ]),
    ).toThrow(/مكرر/);
  });
});
