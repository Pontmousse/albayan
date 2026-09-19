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
    expect(source).toContain("sm:max-w-[96rem]");

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

  it("uses the dedicated lightweight BuTeX preview entry point", () => {
    const source = readLocal("./document-frozen-preview.tsx");

    expect(source).toContain("@drghaliasri/butex/react-document2-preview");
    expect(source).toContain("ButexDocumentPreview");
    expect(source).not.toContain("ButexDocumentEditor2");
    expect(source).not.toContain("previewOnly");
  });
});
