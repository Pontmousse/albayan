import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function readSrc(rel) {
  return readFileSync(join(root, "src", rel), "utf8");
}

const FORBIDDEN_GUIDE_CHROME = [
  /Clerk/i,
  /OAuth/i,
  /\bSettings\b/,
  /\bAccount\b/,
  /\bConnectors\b/,
  /\bDeveloper\b/,
  /\bIntegrations\b/,
  /Edit Config/,
  /get_my_profile/,
  /Streamable HTTP/,
  /\bstdio\b/i,
];

test("mcp-client-guides.ts has no Clerk or English UI chrome in copy", () => {
  const source = readSrc("lib/mcp-client-guides.ts");
  for (const pattern of FORBIDDEN_GUIDE_CHROME) {
    assert.equal(
      pattern.test(source),
      false,
      `forbidden pattern ${pattern} found in mcp-client-guides.ts`,
    );
  }
  assert.match(source, /authLabel: "تسجيل دخول التطبيق"/);
  assert.match(source, /مفتاح ربط/);
  assert.match(source, /سجّل الدخول إلى التطبيق|تسجيل دخول التطبيق/);
});

const WUKALA_SURFACE_FILES = [
  "app/wukala/page.tsx",
  "components/wukala/mcp-client-carousel.tsx",
];

test("wukala page and carousel have no Clerk and no English UI chrome", () => {
  for (const rel of WUKALA_SURFACE_FILES) {
    const source = readSrc(rel);
    for (const pattern of [
      /Clerk/i,
      /OAuth/i,
      /\bSettings\b/,
      /\bConnectors\b/,
      /Streamable HTTP/,
      /\bstdio\b/i,
    ]) {
      assert.equal(
        pattern.test(source),
        false,
        `forbidden pattern ${pattern} found in ${rel}`,
      );
    }
  }
});

test("wukala page and carousel use the locked Arabic headings", () => {
  const page = readSrc("app/wukala/page.tsx");
  const carousel = readSrc("components/wukala/mcp-client-carousel.tsx");
  assert.match(page, /ربط الوكيل الذكي/);
  assert.equal(page.includes("وضع تطوير"), false);
  assert.equal(page.includes("Model Context Protocol"), false);
  assert.match(carousel, /اختر برنامجك واتبع الخطوات/);
  assert.match(carousel, /مثال ملف الربط في Cursor/);
  assert.match(carousel, /سجّل الدخول إلى التطبيق/);
});
