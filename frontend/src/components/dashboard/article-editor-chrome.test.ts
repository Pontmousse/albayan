import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function readLocal(path: string): string {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

describe("focused article editor chrome", () => {
  it("keeps the tahrir route out of the global site header/footer shell", () => {
    const chrome = readLocal("../app-chrome.tsx");

    expect(chrome).toContain("function isEditorChromePath");
    expect(chrome).toContain("tahrir\\/?$/.test(pathname)");
    expect(chrome).toContain(
      "isMinimalChromePath(pathname) || isEditorChromePath(pathname)",
    );
  });

  it("uses one focused Al Bayan editor header and no site-header measurement", () => {
    const page = readLocal(
      "../../app/maktabi/maqalati/[id]/tahrir/page.tsx",
    );

    expect(page).toContain("ArticleEditorHeader");
    expect(page).toContain("--article-editor-actions-height");
    expect(page).not.toContain("data-site-header");
    expect(page).not.toContain("--article-editor-site-header-height");
  });

  it("uses the persisted Al-Bayan numeral preference as BuTeX's digit authority", () => {
    const page = readLocal(
      "../../app/maktabi/maqalati/[id]/tahrir/page.tsx",
    );
    const globals = readLocal("../../app/globals.css");

    expect(page).toContain("formatDigits, numeralSystem");
    expect(page).toContain(
      'digitForm={numeralSystem === "latn" ? "western" : "arabicIndic"}',
    );
    expect(globals).toContain(
      ".albayan-butex-theme .butex-document2-widget__digit-form-menu",
    );
    expect(globals).toContain(
      ".albayan-butex-theme .butex-widget .digit-form-menu",
    );
    expect(globals).toContain(
      ".butex-document2-widget__command-grid--digits",
    );
  });

  it("keeps article tools, workspace navigation, and save state reachable", () => {
    const header = readLocal("./article-editor-header.tsx");

    expect(header).toContain("رموز المعادلات");
    expect(header).toContain("سجل النسخ");
    expect(header).toContain('"صور"');
    expect(header).not.toContain("صور المقال وملفاته");
    expect(header).toContain("تقديم المقال");
    expect(header).toContain("مكتبي");
    expect(header).toContain("مقالاتي");
    expect(header).toContain("الإشعارات");
    expect(header).toContain("إعدادات الحساب");
    expect(header).toContain("SaveStatus");
    expect(header).toContain("MobileSheet");
  });
});
