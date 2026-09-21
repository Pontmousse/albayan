import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function readLocal(path: string): string {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

describe("draft history UI contract", () => {
  it("keeps revision selection summary-first and preview opt-in", () => {
    const source = readLocal("./draft-history-dialog.tsx");

    expect(source).toContain("getDraftRevisionChangeSummary");
    expect(source).toContain("عرض المراجعة كاملة");
    expect(source).toContain("previewOpen && previewDocument");
    expect(source).toContain("selected.is_current && currentDocument && !latestChangesUnsaved");
    expect(source).toContain("md:max-w-[96rem]");

    for (const kind of [
      "added",
      "removed",
      "edited",
      "moved",
      "metadata",
      "other",
    ]) {
      expect(source).toContain(`${kind}:`);
    }
  });

  it("uses a mobile list-to-detail flow and preserves list context", () => {
    const source = readLocal("./draft-history-dialog.tsx");
    const page = readLocal(
      "../../app/maktabi/maqalati/[id]/tahrir/page.tsx",
    );

    expect(source).toContain('type MobileHistoryView = "list" | "detail"');
    expect(source).toContain("listScrollPositionRef");
    expect(source).toContain("function selectRevision");
    expect(source).toContain("function showRevisionList");
    expect(source).toContain("كل النسخ");
    expect(source).toContain('mobileView !== "detail"');
    expect(page).toContain("currentDocument={");
    expect(page).toContain("latestDocumentJson.current");
  });

  it("uses the dedicated lightweight BuTeX preview entry point", () => {
    const source = readLocal("./document-frozen-preview.tsx");

    expect(source).toContain("@drghaliasri/butex/react-document2-preview");
    expect(source).toContain("ButexDocumentPreview");
    expect(source).not.toContain("ButexDocumentEditor2");
    expect(source).not.toContain("previewOnly");
  });
});
