import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("Round 5 canonical BuTeX candidate and UI integration contract", () => {
  it("pins one unpublished BuTeX tarball in manifest and lockfile", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8"));
    const npmLock = JSON.parse(readFileSync("package-lock.json", "utf8"));
    const candidate = JSON.parse(readFileSync("butex-candidate.lock.json", "utf8"));
    expect(pkg.dependencies["@drghaliasri/butex"]).toBe("file:.candidate/butex-candidate.tgz");
    expect(npmLock.packages[""].dependencies["@drghaliasri/butex"]).toBe(pkg.dependencies["@drghaliasri/butex"]);
    expect(npmLock.packages["node_modules/@drghaliasri/butex"].resolved).toBe(pkg.dependencies["@drghaliasri/butex"]);
    expect(candidate.tarball_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(candidate.gitlab_commit).toMatch(/^[a-f0-9]{40}$/);
  });

  it("uses canonical editor, lightweight frozen preview and matching scoped CSS", () => {
    const editor = readFileSync("src/app/maktabi/maqalati/[id]/tahrir/page.tsx", "utf8");
    const preview = readFileSync("src/components/dashboard/document-frozen-preview.tsx", "utf8");
    const mathjax = readFileSync("src/lib/butex-mathjax.ts", "utf8");
    const styles = readFileSync("src/app/globals.css", "utf8");
    expect(editor).toContain("@drghaliasri/butex/react-document");
    expect(editor).toContain("mod.ButexDocumentEditor");
    expect(preview).toContain("@drghaliasri/butex/react-document-preview");
    expect(preview).not.toContain("@drghaliasri/butex/react-document\"");
    expect(mathjax).toContain("injectBuTeXDocumentStyles(document)");
    expect(styles).toContain(".butex-document-widget");
    expect(styles).toContain("--butex-document-accent");
    for (const source of [editor, preview, mathjax, styles]) {
      expect(source).not.toContain("react-document2");
      expect(source).not.toContain("butex-document2-widget");
    }
  });
});
