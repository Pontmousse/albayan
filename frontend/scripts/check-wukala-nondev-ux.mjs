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

test("AgentsNavLink has no DEV or وضع تطوير badge", () => {
  const source = readSrc("components/agents-nav-link.tsx");
  assert.equal(source.includes("DEV"), false);
  assert.equal(source.includes("وضع تطوير"), false);
  assert.match(source, /وكلاء/);
  assert.match(source, /agents-nav-link/);
  assert.match(source, /agents-nav-link__plus/);
});

test("MainNav renders AgentsNavLink on the mobile header, not as a plain list href", () => {
  const source = readSrc("components/main-nav.tsx");
  assert.match(source, /md:hidden[\s\S]*<AgentsNavLink/);
  assert.equal(
    /href:\s*"\/wukala"/.test(source),
    false,
    "do not keep a plain /wukala object inside flatLinks",
  );
  const hiddenDesktopNav = source.slice(
    source.indexOf('className="hidden items-center'),
  );
  assert.match(hiddenDesktopNav, /<AgentsNavLink/);
});

test("MobileSheet is a full-viewport dialog with logical positioning", () => {
  const source = readSrc("components/mobile-sheet.tsx");
  assert.match(source, /export function MobileSheet/);
  assert.match(source, /fixed inset-0/);
  assert.match(source, /role="dialog"/);
  assert.match(source, /إغلاق/);
  assert.equal(/\bleft-/.test(source), false);
  assert.equal(/\bright-/.test(source), false);
  assert.equal(source.includes("absolute end-0"), false);
});

test("MobileNav uses MobileSheet and not an end-0 popover", () => {
  const source = readSrc("components/main-nav.tsx");
  assert.match(source, /import \{ MobileSheet \} from "@\/components\/mobile-sheet"/);
  assert.match(source, /<MobileSheet/);
  assert.match(source, /title="القائمة"/);
  const mobileNavStart = source.indexOf("function MobileNav");
  const mobileNavEnd = source.indexOf("export function MainNav");
  const mobileNav = source.slice(mobileNavStart, mobileNavEnd);
  assert.equal(mobileNav.includes("absolute end-0"), false);
  assert.match(mobileNav, /<AgentsNavLink/);
});

test("AuthHeader uses MobileSheet on mobile and keeps the desktop popover", () => {
  const source = readSrc("components/auth-header.tsx");
  assert.match(source, /import \{ MobileSheet \} from "@\/components\/mobile-sheet"/);
  assert.match(source, /import \{ useMdUp \} from "@\/hooks\/use-md-up"/);
  assert.match(source, /<MobileSheet/);
  assert.match(source, /open=\{sheetOpen\}/);
  assert.match(source, /open && !mdUp/);
  assert.match(source, /title="الحساب"/);
  assert.match(source, /hidden md:block/);
  assert.match(source, /md:hidden/);
  assert.match(source, /absolute start-0 top-full/);
});

test("agent token create UI has no scope checkboxes", () => {
  const source = readSrc("components/settings/agent-tokens-panel.tsx");
  assert.equal(source.includes("الصلاحيات"), false);
  assert.equal(source.includes("toggleScope"), false);
  assert.equal(source.includes("type=\"checkbox\""), false);
  assert.match(source, /scopes: \[\.\.\.ALLOWED_AGENT_SCOPES\]/);
});

test("ChatGPT guide uses accordion motion and a wide connector description", () => {
  const source = readSrc("components/wukala/chatgpt-detailed-guide.tsx");
  assert.match(source, /accordion-panel/);
  assert.match(source, /useOpenTransition/);
  assert.match(source, /صياغة المسودات/);
  assert.match(source, /دون تقديم المقال/);
  assert.equal(source.includes("الوصول إلى ملفي ومقالاتي"), false);
});

test("MCP server URL default is the Railway production endpoint", () => {
  const source = readSrc("lib/mcp-client-guides.ts");
  assert.match(
    source,
    /https:\/\/albayan-mcp-production\.up\.railway\.app\/mcp/,
  );
  assert.equal(source.includes("mcp.albayan-journal.org"), false);
});
