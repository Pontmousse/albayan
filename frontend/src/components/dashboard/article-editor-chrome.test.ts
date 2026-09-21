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

  it("keeps article tools, workspace navigation, and save state reachable", () => {
    const header = readLocal("./article-editor-header.tsx");
    const navigation = readLocal("../albayan-navigation-content.tsx");
    const mainNav = readLocal("../main-nav.tsx");

    expect(header).toContain("رموز المعادلات");
    expect(header).toContain("سجل النسخ");
    expect(header).toContain("صور المقال وملفاته");
    expect(header).toContain("تقديم المقال");
    expect(header).toContain("تفاصيل المقال");
    expect(header).toContain("SaveStatus");
    expect(header).toContain("MobileSheet");
    expect(header).toContain('title="القائمة"');
    expect(header).toContain("أدوات المقال");
    expect(header).toContain("مجلة البيان");
    expect(header).toContain("AlBayanNavigationContent");

    for (const label of ["مكتبي", "مقالاتي", "الإشعارات", "إعدادات الحساب"]) {
      expect(readLocal("../../lib/nav-config.ts")).toContain(label);
    }
    expect(navigation).toContain("workspaceNavLinks");
    expect(navigation).toContain("journalNavLinks");
    expect(navigation).toContain("isMcpEnabled()");
    expect(navigation).toContain("AdminNavLink");
    expect(mainNav).toContain("AlBayanNavigationContent");
  });
});
