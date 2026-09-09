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
  assert.match(source, /سجّل الدخول إلى التطبيق|تسجيل دخول التطبيق/);
  assert.equal(source.includes("ALBAYAN_API_URL"), false);
  assert.equal(source.includes("ALBAYAN_AGENT_TOKEN"), false);
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
  const connection = readSrc("components/wukala/mcp-connection-guide.tsx");
  assert.match(page, /ربط الوكيل الذكي/);
  assert.equal(page.includes("وضع تطوير"), false);
  assert.equal(page.includes("Model Context Protocol"), false);
  assert.match(carousel, /اختر برنامجك واتبع الخطوات/);
  assert.match(connection, /مثال الربط البعيد في/);
  assert.match(connection, /بيانات الربط/);
});

test("wukala intro is concise and does not offer a global token CTA", () => {
  const page = readSrc("app/wukala/page.tsx");
  assert.equal(page.includes("WukalaCtaButton"), false);
  assert.equal(page.includes("Antigravity"), false);
  assert.equal(page.includes("OpenCode"), false);
  assert.match(page, /اربطه بخادم البيان البعيد/);
});

test("AgentsNavLink has no DEV or وضع تطوير badge", () => {
  const source = readSrc("components/agents-nav-link.tsx");
  assert.equal(source.includes("DEV"), false);
  assert.equal(source.includes("وضع تطوير"), false);
  assert.match(source, /وكلاء/);
  assert.match(source, /nav-feature-link--agents/);
  assert.match(source, /nav-feature-link__icon/);
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
  assert.match(source, /import \{?[\s\S]*?MobileSheet,[\s\S]*?\}? from "@\/components\/mobile-sheet"/);
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
  assert.match(source, /import \{?[\s\S]*?MobileSheet,[\s\S]*?\}? from "@\/components\/mobile-sheet"/);
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

test("shared MCP connection guide owns copyable connection data and detailed instructions", () => {
  const source = readSrc("components/wukala/mcp-connection-guide.tsx");
  assert.match(source, /export function McpConnectionGuide/);
  assert.match(source, /MCP_CONNECTION_NAME/);
  assert.match(source, /MCP_CONNECTION_DESCRIPTION/);
  assert.match(source, /MCP_SERVER_URL/);
  assert.match(source, /CopyButton/);
  assert.match(source, /WukalaCtaButton/);
  assert.match(source, /isDevMode\(\).*guide\.id === "cursor" \|\| guide\.id === "other"/s);
  assert.match(source, /accordion-panel/);
  assert.match(source, /useOpenTransition/);
  assert.match(source, /DETAILED_GUIDE_OVERRIDES/);
  assert.match(source, /التعليمات التفصيلية لـ/);
  assert.match(source, /صياغة المسودات/);
  assert.match(source, /دون تقديم المقال/);
  assert.equal(source.includes("الوصول إلى ملفي ومقالاتي"), false);
  assert.ok(
    source.indexOf("<DetailedInstructions") <
      source.indexOf("showAdvancedManualSetup ?"),
    "advanced manual setup must follow the normal remote instructions",
  );
});

test("desktop provider chooser shows every option without horizontal scrolling", () => {
  const source = readSrc("components/wukala/mcp-client-carousel.tsx");
  assert.match(source, /mt-5 hidden gap-2 sm:grid sm:grid-cols-3/);
  assert.match(source, /mt-4 hidden sm:block/);
  assert.match(source, /sm:hidden/);
  assert.match(source, /ArrowLeft/);
  assert.match(source, /ArrowRight/);
  assert.match(source, /Home/);
  assert.match(source, /End/);
  assert.equal(
    source.includes("absolute inset-y-0 start-0 end-0 hidden items-center justify-between sm:flex"),
    false,
  );
});

test("new provider logos are optically enlarged relative to their padded source files", () => {
  const source = readSrc("components/wukala/mcp-client-carousel.tsx");
  assert.match(source, /antigravity:[\s\S]*scale-\[1\.18\]/);
  assert.match(source, /opencode:[\s\S]*scale-\[1\.2\]/);
  assert.match(source, /other:[\s\S]*scale-\[1\.2\]/);
});

test("MCP server URL default is the canonical public endpoint", () => {
  const source = readSrc("lib/mcp-client-guides.ts");
  assert.match(source, /https:\/\/mcp\.albayan-journal\.org\/mcp/);
  assert.equal(source.includes("up.railway.app"), false);
});

test("the MCP carousel offers all six client paths", () => {
  const source = readSrc("lib/mcp-client-guides.ts");
  const ids = ["cursor", "chatgpt", "claude", "antigravity", "opencode", "other"];
  for (const id of ids) assert.match(source, new RegExp(`id: "${id}"`));
  assert.equal((source.match(/\n\s+id: "/g) ?? []).length, 6);
  assert.match(source, /opencode mcp auth albayan/);
  assert.match(source, /لا يحتاج خادم البيان إلى مفتاح API داخل OpenCode/);
  assert.match(source, /"url": "\$\{MCP_SERVER_URL\}"/);
  assert.match(source, /"serverUrl": "\$\{MCP_SERVER_URL\}"/);
  assert.match(source, /"mcp": \{[\s\S]*"servers": \{[\s\S]*"type": "remote"/);
});

test("personal-key surfaces require dev mode while /wukala remains MCP-gated", () => {
  const publicLayout = readSrc("app/wukala/layout.tsx");
  const keyLayout = readSrc("app/al-idayat/wukala/layout.tsx");
  const keyCta = readSrc("components/wukala/wukala-cta-button.tsx");
  const settingsCard = readSrc("components/settings/dev-mode-agents-card.tsx");

  assert.match(publicLayout, /<McpGate>\{children\}<\/McpGate>/);
  assert.equal(publicLayout.includes("DevModeGate"), false);
  assert.match(keyLayout, /<McpGate>[\s\S]*<DevModeGate>\{children\}<\/DevModeGate>/);
  assert.match(keyCta, /if \(!isDevMode\(\)\) \{[\s\S]*return null/);
  assert.match(settingsCard, /if \(!isAgentKeyUiEnabled\(\)\)/);
});

test("advanced agent card follows core account settings", () => {
  const source = readSrc("app/al-idayat/page.tsx");
  assert.ok(source.indexOf("<ProfileForm") < source.indexOf("<DevModeAgentsCard"));
  assert.ok(source.indexOf("<SecurityForm") < source.indexOf("<DevModeAgentsCard"));
  assert.ok(
    source.indexOf("<AccountDeletionRequestCard") <
      source.indexOf("<DevModeAgentsCard"),
  );
});
