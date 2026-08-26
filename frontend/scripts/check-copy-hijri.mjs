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

const COPY_SITES = [
  "components/settings/agent-tokens-panel.tsx",
  "components/wukala/chatgpt-detailed-guide.tsx",
  "components/dashboard/document-json-dev-dialog.tsx",
  "components/dashboard/exported-tex-dev-panel.tsx",
];

test("copy sites use CopyButton and not text copy labels", () => {
  for (const rel of COPY_SITES) {
    const source = readSrc(rel);
    assert.match(source, /CopyButton/, `missing CopyButton in ${rel}`);
    assert.equal(source.includes("نسخ المفتاح"), false, rel);
    assert.equal(source.includes("نسخ TeX"), false, rel);
    assert.equal(source.includes('copied ? "تم النسخ"'), false, rel);
  }
});

test("Umm al-Qura formats 2026-08-26 as ١٣ ربيع الأول ١٤٤٨ هـ", () => {
  const formatter = new Intl.DateTimeFormat("ar-SA-u-ca-islamic-umalqura", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  assert.equal(formatter.resolvedOptions().calendar, "islamic-umalqura");
  assert.equal(
    formatter.format(new Date("2026-08-26T12:00:00Z")),
    "١٣ ربيع الأول ١٤٤٨ هـ",
  );
});

test("format-date.ts uses ar-SA islamic-umalqura", () => {
  const source = readSrc("lib/format-date.ts");
  assert.match(source, /ar-SA-u-ca-islamic-umalqura/);
  assert.match(source, /export function formatDateTime/);
  assert.match(source, /export function formatHijriYear/);
});
