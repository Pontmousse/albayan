import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function readLocal(path: string): string {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

describe("issue 142 authoring UX follow-up", () => {
  it("uses an owned accessible visual mapping picker", () => {
    const selector = readLocal("./mapping-font-selector.tsx");
    const fonts = readLocal("../../lib/mapping-fonts.ts");

    expect(selector).not.toContain("<select");
    expect(selector).toContain('aria-haspopup="listbox"');
    expect(selector).toContain('role="listbox"');
    expect(selector).toContain('role="option"');
    expect(selector).toContain("ArrowDown");
    expect(selector).toContain("Escape");
    expect(selector).toContain("متقدم");
    expect(selector).toContain("أبجد هوز");
    expect(fonts).toContain('latexCommand: "butextakween"');
    expect(fonts).toContain('latexCommand: "butexdiwani"');
    expect(fonts).toContain('latexCommand: "butexdiwanioutline"');
    expect(fonts).toContain('latexCommand: "butexmaghribi"');
    expect(fonts).toContain('id: "none"');
    expect(fonts).toContain("للحالات المتقدمة");
  });

  it("keeps technical mapping serialization in DEV mode only", () => {
    const panel = readLocal("./equation-mappings-panel.tsx");

    expect(panel).toContain('import { isDevMode } from "@/lib/dev-mode"');
    expect(panel).toContain("const showTechnicalPreview = isDevMode()");
    expect(panel).toContain("showTechnicalPreview ? (");
    expect(panel).toContain("معاينة الصيغة التقنية");
    expect(panel).not.toContain("BuTeX");
    expect(panel).not.toContain("LaTeX");
    expect(panel).toContain("أدوات البيان الذكية");
    expect(panel).toContain('href="/wukala"');
    expect(panel).toContain('fontId: "default"');
  });

  it("uses a mobile list to revision-detail drill-down without eager preview", () => {
    const history = readLocal("./draft-history-dialog.tsx");

    expect(history).toContain("mobileDetailOpen");
    expect(history).toContain("mobileListScrollTopRef");
    expect(history).toContain("showMobileRevisionList");
    expect(history).toContain("كل النسخ");
    expect(history).toContain("togglePreview");
    expect(history).toContain("getDraftRevisionChangeSummary");
    expect(history).toContain("getDraftRevision(getToken");
    expect(history).not.toContain("selectRevision = async");
  });

  it("shares the learned mobile navigation model with the article editor", () => {
    const shared = readLocal("../mobile-navigation-content.tsx");
    const mainNav = readLocal("../main-nav.tsx");
    const editor = readLocal("./article-editor-header.tsx");

    expect(shared).toContain("export function MobileNavigationContent");
    expect(shared).toContain("navGroups.flatMap");
    expect(shared).toContain("NumeralToggle mobile");
    expect(mainNav).toContain("<MobileNavigationContent onNavigate={close} />");
    expect(editor).toContain("<MobileNavigationContent");
    expect(editor).toContain('title="القائمة"');
    expect(editor).toContain("contextualContent={mobileArticleContext}");
    expect(editor).toContain("رموز المعادلات");
    expect(editor).toContain("سجل النسخ");
  });
});
