import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const panel = readFileSync(new URL("./units-panel.tsx", import.meta.url), "utf8");

describe("units panel navigation", () => {
  it("starts with category cards and has an explicit way back", () => {
    expect(panel).toContain('selectedGroup === null');
    expect(panel).toContain('GROUP_ICONS[group.key]');
    expect(panel).toContain('navigateToGroup(group.key)');
    expect(panel).toContain('navigateToGroup(null)');
    expect(panel).toContain('grid-cols-1 gap-3 sm:grid-cols-2');
  });

  it("edits conventions using accessible in-panel choices, not a native picker", () => {
    expect(panel).not.toContain("<select");
    expect(panel).toContain('aria-pressed={active}');
    expect(panel).toContain('aria-pressed={customMode}');
    expect(panel).toContain('aria-expanded={isEditing}');
    expect(panel).toContain('chooseKnownDisplay(unit, "__custom__")');
  });

  it("keeps custom units and the revision-safe apply path", () => {
    expect(panel).toContain('navigateToGroup("custom")');
    expect(panel).toContain("validateUnitConventions(");
    expect(panel).toContain("applyUnitConventions(getToken, articleId, baseRevision, next)");
  });
});
