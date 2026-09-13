import { describe, expect, it } from "vitest";
import {
  formatAnalyticsBucket,
  formatDate,
  formatDateTime,
  formatHijriYear,
  formatRelativeTime,
} from "./format-date";
import { normalizeDigits } from "./numerals";

const DATE = new Date("2026-09-01T12:30:00.000Z");

describe("Hijri date formatting", () => {
  it("keeps Umm al-Qura output while switching digit systems", () => {
    const arab = formatDate(DATE.toISOString(), "arab");
    const latn = formatDate(DATE.toISOString(), "latn");
    expect(arab).toMatch(/[٠-٩]/);
    expect(latn).toMatch(/[0-9]/);
    expect(normalizeDigits(arab)).toBe(latn);
    expect(latn).toMatch(/[\u0600-\u06ff]/);
  });

  it("formats date-time, year, and relative time in both systems", () => {
    expect(formatDateTime(DATE, "arab")).toMatch(/[٠-٩]/);
    expect(formatDateTime(DATE, "latn")).toMatch(/[0-9]/);
    expect(formatHijriYear(DATE, "arab")).toMatch(/[٠-٩]/);
    expect(formatHijriYear(DATE, "latn")).toMatch(/[0-9]/);

    const fiveMinutesAgo = new Date(DATE.getTime() - 5 * 60 * 1000).toISOString();
    expect(formatRelativeTime(fiveMinutesAgo, DATE, "arab")).toContain("٥");
    expect(formatRelativeTime(fiveMinutesAgo, DATE, "latn")).toContain("5");
  });

  it("formats analytics chart buckets through the Umm al-Qura utility", () => {
    const day = formatAnalyticsBucket(DATE.toISOString(), "day", "latn");
    const hour = formatAnalyticsBucket(DATE.toISOString(), "hour", "arab");
    expect(day).toMatch(/[0-9]/);
    expect(day).toMatch(/[\u0600-\u06ff]/);
    expect(hour).toMatch(/[٠-٩]/);
  });
});
