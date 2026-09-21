import { readFileSync, statSync } from "node:fs";
import { describe, expect, it } from "vitest";

function readLocal(path: string): string {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

describe("equation mapping author UI", () => {
  it("uses the accessible Al Bayan visual picker instead of a native select", () => {
    const selector = readLocal("./mapping-font-selector.tsx");
    const responsiveSelect = readLocal("../ui/responsive-select.tsx");

    expect(selector).toContain("ResponsiveSelect");
    expect(selector).toContain("renderSelected");
    expect(selector).toContain("renderOption");
    expect(selector).toContain("أبجد هوز");
    expect(selector).not.toContain("<select");
    expect(responsiveSelect).toContain('role="combobox"');
    expect(responsiveSelect).toContain('role="listbox"');
    expect(responsiveSelect).toContain('event.key === "ArrowDown"');
    expect(responsiveSelect).toContain('event.key === "Escape"');
  });

  it("keeps technical syntax in DEV and restores the author motivation", () => {
    const panel = readLocal("./equation-mappings-panel.tsx");

    expect(panel).toContain("isDevMode()");
    expect(panel).toContain("showDevDiagnostics ? (");
    expect(panel).toContain("معاينة الصيغة التقنية");
    expect(panel).toContain("تساعد اختياراتك أدوات البيان الذكية");
    expect(panel).toContain("isMcpEnabled()");
    expect(panel).not.toContain("LaTeX");
    expect(panel).not.toContain("BuTeX");
  });

  it("ships each local browser preview font", () => {
    for (const filename of [
      "../../../public/Takween.otf",
      "../../../public/Diwani Letter Regular.ttf",
      "../../../public/DWNOUTSH.TTF",
      "../../../public/Almaghribi-Warsh-Quran.otf",
    ]) {
      expect(statSync(new URL(filename, import.meta.url)).size).toBeGreaterThan(
        1_000,
      );
    }
  });
});
