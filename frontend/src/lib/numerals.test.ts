import { describe, expect, it } from "vitest";
import {
  formatDigits,
  formatNumber,
  normalizeDigits,
  normalizeNumericInput,
  parseBoundedInteger,
} from "./numerals";

describe("numeral utilities", () => {
  it("formats application-owned mixed strings in either system", () => {
    expect(formatDigits("v12 · 99+", "arab")).toBe("v١٢ · ٩٩+");
    expect(formatDigits("v۱۲ · ٩٩+", "latn")).toBe("v12 · 99+");
  });

  it("normalizes Arabic and Persian digits to ASCII", () => {
    expect(normalizeDigits("٠١٢٣٤٥٦٧٨٩")).toBe("0123456789");
    expect(normalizeDigits("۰۱۲۳۴۵۶۷۸۹")).toBe("0123456789");
  });

  it("formats negative, decimal, grouped, and percentage values", () => {
    const arab = [
      formatNumber(-12.5, "arab"),
      formatNumber(12345, "arab"),
      formatNumber(0.25, "arab", { style: "percent" }),
    ].join(" ");
    const latn = [
      formatNumber(-12.5, "latn"),
      formatNumber(12345, "latn"),
      formatNumber(0.25, "latn", { style: "percent" }),
    ].join(" ");
    expect(arab).toMatch(/[٠-٩]/);
    expect(arab).not.toMatch(/[0-9]/);
    expect(latn).toMatch(/[0-9]/);
    expect(latn).not.toMatch(/[٠-٩]/);
  });

  it("validates numeric input without silently dropping invalid characters", () => {
    expect(normalizeNumericInput(" ١۲3 ", 3)).toBe("123");
    expect(normalizeNumericInput("١a", 3)).toBeNull();
    expect(normalizeNumericInput("١٢٣٤", 3)).toBeNull();
    expect(normalizeNumericInput("", 3)).toBe("");
    expect(parseBoundedInteger("1", 1, 365)).toBe(1);
    expect(parseBoundedInteger("365", 1, 365)).toBe(365);
    expect(parseBoundedInteger("", 1, 365)).toBeNull();
    expect(parseBoundedInteger("0", 1, 365)).toBeNull();
    expect(parseBoundedInteger("366", 1, 365)).toBeNull();
    expect(parseBoundedInteger("1.5", 1, 365)).toBeNull();
  });
});
