import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
function readSrc(rel) {
  return readFileSync(join(root, "src", rel), "utf8");
}

test("CopyButton is an icon-only clipboard control", () => {
  const source = readSrc("components/ui/copy-button.tsx");
  assert.match(source, /export function CopyButton/);
  assert.match(source, /navigator\.clipboard\.writeText/);
  assert.match(source, /aria-label/);
  assert.match(source, /copy-button/);
  assert.equal(source.includes("نسخ المفتاح"), false);
});
