# Wukala Non-Developer UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/wukala` and the Agents header control usable for a non-teacher, non-developer: Arabic-only instructions, no Clerk in copy, a visible emerald Agents control on phones, and a full-viewport mobile menu so RTL popover placement no longer matters.

**Architecture:** Copy lives in `frontend/src/lib/mcp-client-guides.ts` and the `/wukala` page/carousel; a `node --test` source-contract script guards forbidden English/Clerk/DEV strings. The distinctive `AgentsNavLink` pill is rendered in the header on all breakpoints when `isDevMode()` is true. Mobile `القائمة` and the signed-in account menu stop using `absolute end-0 top-full` popovers and instead open a shared `MobileSheet` (`fixed inset-0`). Desktop `NavDropdown` and the desktop account popover stay as they are.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind 4 (logical properties), Node.js built-in test runner (`node --test`). No new npm dependencies. Clerk remains an implementation detail (`useAuth` / `AppClerkProvider`) and must never appear in user-visible strings.

## Global Constraints

- User-visible auth copy is only `تسجيل دخول التطبيق` or `سجّل الدخول إلى التطبيق` — never `Clerk`, never `OAuth`.
- Instruction UI chrome is Arabic: `إعدادات` not `Settings`; `حساب` not `Account`; `أدوات الربط` not `Connectors` / `Connect`; `للمطوّرين` not `Developer`; `التكاملات` not `Integrations`; `تعديل ملف الإعداد` not `Edit Config`.
- Agent credential in user copy is `مفتاح ربط` (the `alb_…` prefix may appear once as an example). Do not write `API token` or `API key`.
- Product names `Cursor`, `ChatGPT`, `Claude`, `claude.ai`, and the letters `MCP` may remain. JSON/env keys in the Cursor snippet may remain (`ALBAYAN_AGENT_TOKEN`, `mcpServers`).
- Remove the visible `DEV` / `وضع تطوير` badge from `AgentsNavLink` only. Keep `isDevMode()` / `NEXT_PUBLIC_DEV_MODE` / `DevModeGate` unchanged.
- Root document is `lang="ar"` `dir="rtl"`. New/changed Tailwind uses logical properties (`ms-`, `me-`, `ps-`, `pe-`, `start`, `end`, `inset-inline-*`) — not `left-` / `right-`.
- Mobile menus that currently use `absolute end-0 top-full`: replace with a full-viewport sheet. Desktop placement of the same menus stays correct and is not restyled.
- No database logic or secrets in `frontend/`. Browser calls go through `NEXT_PUBLIC_API_URL`.
- Do not add Vitest, Jest, Playwright, or Testing Library. Contracts are `node --test` on source text plus `npm run lint` plus browser verification.
- Do not rename Clerk packages, hooks, or provider files. Out of scope: `/al-idayat/wukala` token CRUD, backend, MCP server, policies page Clerk mention, admin Clerk mention.

## File map

| File | Responsibility |
| ---- | -------------- |
| Create: `frontend/scripts/check-wukala-nondev-ux.mjs` | Source-contract tests (Clerk/English chrome/DEV/mobile sheet). |
| Modify: `frontend/package.json` | Add `test:wukala-ux` script. |
| Modify: `frontend/src/lib/mcp-client-guides.ts` | All client walkthrough copy (Cursor / ChatGPT / Claude). |
| Modify: `frontend/src/app/wukala/page.tsx` | Hero and MCP explainer in plain Arabic. |
| Modify: `frontend/src/components/wukala/mcp-client-carousel.tsx` | Section titles and helper sentences in Arabic; no `stdio` in visible labels. |
| Modify: `frontend/src/components/agents-nav-link.tsx` | Delete `DEV` badge; keep emerald pill + `+`. |
| Create: `frontend/src/components/mobile-sheet.tsx` | Full-viewport sheet used by mobile nav and mobile account menu. |
| Modify: `frontend/src/components/main-nav.tsx` | Show `AgentsNavLink` on mobile header; `MobileNav` uses `MobileSheet`. |
| Modify: `frontend/src/components/auth-header.tsx` | Signed-in mobile menu uses `MobileSheet`; desktop popover unchanged. |

**Do not modify:** `frontend/src/lib/dev-mode.ts`, `frontend/src/components/dev-mode-gate.tsx`, `frontend/src/app/wukala/layout.tsx`, `frontend/src/components/wukala/wukala-cta-button.tsx` (CTA text `أنشئ مفتاحك الخاص` stays), `frontend/src/app/globals.css` (keep `.agents-nav-link` shimmer).

## Locked decisions (do not re-open)

1. **Which menu is broken:** `MobileNav` in `frontend/src/components/main-nav.tsx` (button label `القائمة`, panel `absolute end-0 top-full`). In RTL `end` is the visual left, so the panel hangs left-and-down of the trigger. The MCP carousel has **no** dropdown. Also fix the signed-in `AuthHeader` menu — same `absolute end-0 top-full` class — with a mobile sheet; keep its desktop popover.
2. **Desktop stays:** `NavDropdown` (`absolute start-0 top-full`) and `AuthHeader` desktop popover (`hidden md:block` + existing `absolute end-0 top-full`) are not restyled.
3. **Agents on a phone:** `AgentsNavLink` is rendered in a `md:hidden` wrapper in the header cluster (sibling of `MobileNav`), so the emerald pill is visible without opening `القائمة`. Remove the plain `{ href: "/wukala", label: "وكلاء" }` entry from `flatLinks`. Put one highlighted `AgentsNavLink` at the top of the mobile sheet as well (same component, not a third unstyled row).
4. **Clerk in code:** `useAuth` from `@clerk/nextjs` and `AppClerkProvider` stay. Only user-visible strings change.
5. **Cursor snippet:** Keep `CURSOR_MCP_STDIO_SNIPPET`. Retitle it in Arabic. Do not invent a new non-stdio Cursor path.
6. **Page eyebrow:** Replace `وضع تطوير · MCP` with `ربط الوكيل الذكي`. This is page copy, not the `DEV_MODE` gate.

---

### Task 1: Source-contract test + Arabic client guides

**Files:**
- Create: `frontend/scripts/check-wukala-nondev-ux.mjs`
- Modify: `frontend/package.json` (scripts only)
- Modify: `frontend/src/lib/mcp-client-guides.ts`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: existing `McpClientGuide` / `MCP_CLIENT_GUIDES` in `frontend/src/lib/mcp-client-guides.ts`
- Produces: npm script `test:wukala-ux` → `node --test scripts/check-wukala-nondev-ux.mjs`; user-visible ChatGPT/Claude `authLabel` must be exactly `تسجيل دخول التطبيق`; Cursor `authLabel` must include `مفتاح ربط`

- [ ] **Step 1: Write the failing contract test and npm script**

Create `frontend/scripts/check-wukala-nondev-ux.mjs` with this exact content:

```js
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
```

In `frontend/package.json`, change only the `scripts` object to:

```json
  "scripts": {
    "dev": "next dev",
    "dev:clean": "npm run clean && next dev",
    "clean": "node -e \"require('fs').rmSync('.next',{recursive:true,force:true}); console.log('Removed .next')\"",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test:wukala-ux": "node --test scripts/check-wukala-nondev-ux.mjs"
  },
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL. At least one assertion fires because the current file contains `Clerk`, `OAuth`, `Connectors`, `Developer`, `Edit Config`, `get_my_profile`, `Streamable HTTP`, and `stdio`. Example line:

```text
AssertionError: forbidden pattern /Clerk/i found in mcp-client-guides.ts
```

If the script is missing, Node prints `Cannot find module` — that also counts as fail; keep the file from Step 1.

- [ ] **Step 3: Replace the three guides with the Arabic copy below**

In `frontend/src/lib/mcp-client-guides.ts`, keep the types, `MCP_SERVER_URL`, `MCP_API_URL`, and `CURSOR_MCP_STDIO_SNIPPET` exactly as they are. Replace only the `MCP_CLIENT_GUIDES` array with:

```ts
export const MCP_CLIENT_GUIDES: McpClientGuide[] = [
  {
    id: "cursor",
    name: "Cursor",
    tagline: "برنامج على الحاسوب — تربطه بمفتاح ربط من حسابك",
    accentClass: "from-slate-700 to-slate-900",
    authLabel: "مفتاح ربط (يبدأ بـ alb_…)",
    desktopSteps: [
      "من هذه الصفحة اضغط «أنشئ مفتاحك الخاص». إن لم تكن داخل حسابك سيُطلب منك تسجيل دخول التطبيق أولاً.",
      "انسخ مفتاح الربط فور ظهوره (يُعرض مرة واحدة فقط).",
      "افتح برنامج Cursor على الحاسوب.",
      "من Cursor: إعدادات ← MCP ← أضف خادماً جديداً، واختر الربط من الجهاز.",
      "ضع مفتاح الربط في خانة ALBAYAN_AGENT_TOKEN كما في مثال ملف الربط أدناه.",
      "أعد تشغيل Cursor، ثم اكتب: «ما هو ملفي في مجلة البيان؟»",
    ],
    mobileSteps: [
      "تطبيق Cursor على الجوال لا يدعم هذا الربط بشكل كامل حالياً.",
      "أكمل الخطوات من الحاسوب. مفتاح الربط نفسه يعمل على أي جهاز تُعدّه لاحقاً.",
    ],
    notes: [
      "هذا المسار يناسب من يستخدم Cursor على حاسوبه.",
      "احفظ مفتاح الربط في مكان خاص؛ لا تنشره ولا ترسله لأحد.",
    ],
  },
  {
    id: "chatgpt",
    name: "ChatGPT",
    tagline: "من الموقع أو التطبيق — تربطه بتسجيل دخول التطبيق",
    accentClass: "from-emerald-600 to-teal-800",
    authLabel: "تسجيل دخول التطبيق",
    desktopSteps: [
      "افتح ChatGPT على الحاسوب.",
      "اضغط صورتك أو اسمك في الشريط، ثم اختر إعدادات.",
      "من الإعدادات افتح التطبيقات ثم أدوات الربط، واضغط إضافة MCP.",
      "الصق عنوان الخادم الظاهر في الصندوق أدناه.",
      "عندما تظهر نافذة الدخول: سجّل الدخول إلى التطبيق ووافق على الصلاحيات.",
      "ارجع إلى المحادثة واسأل: «استخدم أداة البيان وأعطني ملفي الشخصي».",
    ],
    mobileSteps: [
      "افتح تطبيق ChatGPT على الجوال.",
      "من القائمة: إعدادات ← التطبيقات ← أدوات الربط (إن ظهرت في إصدار تطبيقك).",
      "الصق عنوان الخادم نفسه الظاهر أدناه.",
      "إن فُتح المتصفح: سجّل الدخول إلى التطبيق ثم عد إلى ChatGPT.",
    ],
    notes: [
      "لا تحتاج إلى نسخ مفتاح ربط يدوياً — يكفي تسجيل دخول التطبيق.",
      "في هذه المرحلة يقرأ الوكيل ملفك ومقالاتك فقط؛ التقديم يبقى من منصة البيان.",
    ],
  },
  {
    id: "claude",
    name: "Claude",
    tagline: "من claude.ai أو تطبيق الحاسوب — تربطه بتسجيل دخول التطبيق",
    accentClass: "from-amber-700 to-orange-900",
    authLabel: "تسجيل دخول التطبيق",
    desktopSteps: [
      "من موقع claude.ai: إعدادات ← التكاملات ← أضف خادم MCP.",
      "أو من تطبيق Claude على الحاسوب: إعدادات ← للمطوّرين ← تعديل ملف الإعداد، ثم أضف الخادم.",
      "الصق عنوان الخادم الظاهر في الصندوق أدناه.",
      "عندما يُطلب منك: سجّل الدخول إلى التطبيق ووافق على الصلاحيات.",
      "اسأل: «اعرض ملفي في مجلة البيان».",
    ],
    mobileSteps: [
      "افتح تطبيق Claude على الجوال.",
      "إن ظهر خيار الربط أو التكاملات: الصق عنوان الخادم نفسه.",
      "إن لم يظهر الخيار في إصدار تطبيقك، أكمل الربط من المتصفح أو من الحاسوب.",
    ],
    notes: [
      "التقديم والحفظ يبقيان يدوياً من منصة البيان.",
      "إن كنت تستخدم Cursor أصلاً يمكنك بدل ذلك إنشاء مفتاح ربط واستخدامه هناك.",
    ],
  },
];
```

Do not leave `Clerk`, `OAuth`, `Connectors`, `Developer`, `Integrations`, `Edit Config`, `get_my_profile`, `Streamable HTTP`, or `stdio` anywhere in this file (including comments and taglines). The JSON snippet below the array already contains `mcpServers` and env keys — that is allowed and is **outside** the array; do not put the word `stdio` in a comment above the snippet either. If a file-level comment currently says `stdio`, delete that word from the comment.

- [ ] **Step 4: Run the test and confirm it passes**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected:

```text
# pass 1
# fail 0
```

or Node’s equivalent summary with 1 passing test and exit code 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/package.json frontend/src/lib/mcp-client-guides.ts
git commit -m "feat(wukala): أدلة العملاء بالعربية دون ذكر Clerk"
```

---

### Task 2: `/wukala` page and carousel copy

**Files:**
- Modify: `frontend/src/app/wukala/page.tsx`
- Modify: `frontend/src/components/wukala/mcp-client-carousel.tsx`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: `MCP_CLIENT_GUIDES`, `CURSOR_MCP_STDIO_SNIPPET`, `MCP_SERVER_URL` from `@/lib/mcp-client-guides` (unchanged exports)
- Produces: page eyebrow text `ربط الوكيل الذكي`; carousel heading `اختر برنامجك واتبع الخطوات`; Cursor snippet heading `مثال ملف الربط في Cursor`

- [ ] **Step 1: Extend the contract test (must fail)**

Append these two tests to `frontend/scripts/check-wukala-nondev-ux.mjs` (keep the Task 1 test in place):

```js
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
```

- [ ] **Step 2: Run tests and confirm the new ones fail**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL on the new tests. Current `page.tsx` still has `وضع تطوير · MCP` and `Model Context Protocol (MCP)`. Current carousel still has `مثال إعداد Cursor (stdio)` and `Streamable HTTP`. Task 1 test remains PASS.

- [ ] **Step 3: Rewrite the page hero and MCP explainer**

Replace the contents of `frontend/src/app/wukala/page.tsx` with:

```tsx
import type { Metadata } from "next";
import Link from "next/link";
import { McpClientCarousel } from "@/components/wukala/mcp-client-carousel";
import { WukalaCtaButton } from "@/components/wukala/wukala-cta-button";

export const metadata: Metadata = {
  title: "الوكلاء | البيان",
  description:
    "اربط وكيلك الذكي بمجلة البيان — Cursor أو ChatGPT أو Claude.",
};

export default function WukalaPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-14">
        <p className="text-xs font-semibold text-emerald-700">
          ربط الوكيل الذكي
        </p>
        <h1
          className="mt-3 text-balance text-3xl font-bold text-slate-900 sm:text-4xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          اربط وكيلك الذكي بمجلة البيان
        </h1>
        <p className="mt-4 text-pretty text-sm leading-7 text-slate-600 sm:text-base">
          اختر برنامجك (
          <strong className="font-semibold text-slate-800">Cursor</strong> أو{" "}
          <strong className="font-semibold text-slate-800">ChatGPT</strong> أو{" "}
          <strong className="font-semibold text-slate-800">Claude</strong>
          ) واتبع الخطوات. البرنامج يساعدك في الكتابة، وأنت تحفظ وتقدّم من
          منصة البيان.
        </p>

        <div className="mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <WukalaCtaButton className="w-full sm:w-auto" />
          <Link
            href="/irshadat-al-mualifin"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)]"
          >
            إرشادات المؤلفين
          </Link>
        </div>

        <McpClientCarousel />

        <section className="mt-10 rounded-2xl border border-[var(--journal-border)] bg-white/80 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">كيف يعمل الربط؟</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">
            الربط يعني أن برنامج الذكاء الاصطناعي يرى ملفك في المجلة بعد أن
            تسمح له. نسمّي هذه الصلة MCP. لا يقدّم المقال عنك ولا يتّخذ قرارات
            التحرير.
          </p>
        </section>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <section className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
            <h2 className="text-sm font-bold text-emerald-900">ما يفعله الوكيل</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-emerald-950/80">
              <li>قراءة ملفك ومقالاتك</li>
              <li>مساعدة في الكتابة (مسودة الجلسة — قريباً)</li>
              <li>مسودة ملاحظات المراجعة</li>
            </ul>
          </section>
          <section className="rounded-xl border border-amber-200 bg-amber-50/50 p-5">
            <h2 className="text-sm font-bold text-amber-900">ما لا يفعله</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-950/80">
              <li>تقديم المقال نيابة عنك</li>
              <li>إرسال تقرير المراجعة</li>
              <li>قرارات التحرير أو الإدارة</li>
            </ul>
          </section>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Rewrite visible carousel chrome**

In `frontend/src/components/wukala/mcp-client-carousel.tsx`, make these exact string replacements (leave component logic, refs, and class names unchanged):

Replace:

```tsx
            تفعيل الخادم حسب عميلك
```

with:

```tsx
            اختر برنامجك واتبع الخطوات
```

Replace:

```tsx
            اسحب البطاقات يميناً ويساراً — أو اختر من الأزرار أدناه
```

with:

```tsx
            اسحب البطاقات أو اضغط اسم البرنامج أعلاه
```

Replace:

```tsx
            مثال إعداد Cursor (stdio)
```

with:

```tsx
            مثال ملف الربط في Cursor
```

Replace:

```tsx
            استبدل <code className="rounded bg-slate-100 px-1">alb_…</code> بمفتاحك
            بعد إنشائه.
```

with:

```tsx
            استبدل <code className="rounded bg-slate-100 px-1">alb_…</code> بمفتاح
            الربط بعد إنشائه.
```

Replace:

```tsx
            Streamable HTTP — سجّل الدخول عند الطلب. لا حاجة لنسخ مفتاح يدوياً.
```

with:

```tsx
            هذا العنوان هو صلة الوصل. سجّل الدخول إلى التطبيق عندما يُطلب منك —
            دون نسخ مفتاح ربط.
```

Leave `عنوان الخادم (URL)` as `عنوان الخادم` (drop the Latin `(URL)`):

```tsx
          <p className="text-sm font-semibold text-slate-800">عنوان الخادم</p>
```

- [ ] **Step 5: Run tests and lint**

Run:

```bash
cd frontend && npm run test:wukala-ux && npm run lint
```

Expected: all `test:wukala-ux` tests PASS (3 tests). Lint: no errors in the two edited files. `next lint` may report pre-existing warnings elsewhere; do not “fix” unrelated files. If lint fails on these two files, fix only those failures and re-run.

- [ ] **Step 6: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/src/app/wukala/page.tsx frontend/src/components/wukala/mcp-client-carousel.tsx
git commit -m "feat(wukala): تبسيط نص الصفحة والعرض الدوّار لغير المختصين"
```

---

### Task 3: Remove the `DEV` badge from the Agents nav pill

**Files:**
- Modify: `frontend/src/components/agents-nav-link.tsx`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: none
- Produces: `export function AgentsNavLink(): JSX.Element` — same export name, no new props, still links to `/wukala`, still uses classes `agents-nav-link` and `agents-nav-link__plus`

- [ ] **Step 1: Add the failing badge contract**

Append to `frontend/scripts/check-wukala-nondev-ux.mjs`:

```js
test("AgentsNavLink has no DEV or وضع تطوير badge", () => {
  const source = readSrc("components/agents-nav-link.tsx");
  assert.equal(source.includes("DEV"), false);
  assert.equal(source.includes("وضع تطوير"), false);
  assert.match(source, /وكلاء/);
  assert.match(source, /agents-nav-link/);
  assert.match(source, /agents-nav-link__plus/);
});
```

- [ ] **Step 2: Run and confirm fail**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL with `source.includes("DEV")` is `true` (the amber `DEV` span is still in the component). Previous tests PASS.

- [ ] **Step 3: Delete the badge and tighten mobile padding**

Replace the entire contents of `frontend/src/components/agents-nav-link.tsx` with:

```tsx
"use client";

import Link from "next/link";

export function AgentsNavLink() {
  return (
    <Link
      href="/wukala"
      className="agents-nav-link group inline-flex min-h-10 items-center gap-1.5 rounded-full border border-emerald-500/45 bg-gradient-to-br from-emerald-50/90 to-white px-2.5 py-1 text-xs font-semibold text-emerald-900 shadow-sm transition-shadow duration-300 hover:shadow-md sm:px-3 sm:text-sm"
    >
      <span
        className="agents-nav-link__plus inline-flex h-5 w-5 items-center justify-center rounded-full bg-[var(--journal-accent)] text-xs font-bold text-white"
        aria-hidden
      >
        +
      </span>
      <span>وكلاء</span>
    </Link>
  );
}
```

Do not remove `isDevMode()` from `main-nav.tsx` in this task. Do not edit `frontend/src/lib/dev-mode.ts`.

- [ ] **Step 4: Run tests**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: all tests PASS, including the new badge test. Exit code 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/src/components/agents-nav-link.tsx
git commit -m "fix(nav): إزالة شارة DEV من زر الوكلاء"
```

---

### Task 4: Show the emerald Agents pill on the mobile header

**Files:**
- Modify: `frontend/src/components/main-nav.tsx`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: `export function AgentsNavLink(): JSX.Element` from `@/components/agents-nav-link`; `isDevMode()` from `@/lib/dev-mode`
- Produces: when `isDevMode()` is true, `MainNav` renders `<div className="md:hidden"><AgentsNavLink /></div>` as a sibling of `MobileNav` (not inside `className="hidden … md:flex"`). `flatLinks` no longer appends `{ href: "/wukala", label: "وكلاء" }`

- [ ] **Step 1: Add the failing header-placement contract**

Append to `frontend/scripts/check-wukala-nondev-ux.mjs`:

```js
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
```

- [ ] **Step 2: Run and confirm fail**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL. Current `MainNav` only mounts `AgentsNavLink` inside the `hidden … md:flex` nav, and `flatLinks` still has `href: "/wukala"`.

- [ ] **Step 3: Place the pill on mobile and drop the plain list row**

In `frontend/src/components/main-nav.tsx`, change `flatLinks` to:

```ts
  const flatLinks = [
    primaryNavLink,
    ...navGroups.flatMap((g) => g.items),
    contactNavLink,
  ];
```

Change `export function MainNav` to:

```tsx
export function MainNav() {
  return (
    <>
      {isDevMode() ? (
        <div className="md:hidden">
          <AgentsNavLink />
        </div>
      ) : null}
      <MobileNav />
      <nav
        aria-label="التنقل الرئيسي"
        className="hidden items-center gap-0.5 md:flex"
      >
        <NavTextLink href={primaryNavLink.href} label={primaryNavLink.label} />
        {navGroups.map((group) => (
          <NavDropdown key={group.label} group={group} />
        ))}
        <NavTextLink href={contactNavLink.href} label={contactNavLink.label} />
        {isDevMode() ? <AgentsNavLink /> : null}
      </nav>
    </>
  );
}
```

Do not restyle `AgentsNavLink` again. Do not change `MobileNav`’s `absolute end-0` panel in this task.

- [ ] **Step 4: Run tests**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: PASS, including the new placement test. Exit code 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/src/components/main-nav.tsx
git commit -m "fix(nav): إظهار زر الوكلاء المميّز في ترويسة الجوال"
```

---

### Task 5: Full-viewport `MobileSheet` + `القائمة`

**Files:**
- Create: `frontend/src/components/mobile-sheet.tsx`
- Modify: `frontend/src/components/main-nav.tsx`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: `AgentsNavLink`, `isDevMode()`, existing `flatLinks` / `useMenuDismiss`
- Produces:

```ts
export function MobileSheet(props: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}): JSX.Element | null
```

`MobileSheet` returns `null` when `open` is false. When open it renders `role="dialog"` `aria-modal="true"` with `className` containing `fixed inset-0` (no `absolute`, no `left-`, no `right-`). Close control visible text is `إغلاق`.

- [ ] **Step 1: Add the failing sheet contracts**

Append to `frontend/scripts/check-wukala-nondev-ux.mjs`:

```js
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
```

- [ ] **Step 2: Run and confirm fail**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL — `components/mobile-sheet.tsx` does not exist (`ENOENT`) and `MobileNav` still contains `absolute end-0`.

- [ ] **Step 3: Create `MobileSheet`**

Create `frontend/src/components/mobile-sheet.tsx` with this exact content:

```tsx
"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

export function MobileSheet({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col bg-[var(--journal-paper)] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      <div className="flex items-center justify-between gap-3 border-b border-emerald-200/80 bg-gradient-to-l from-emerald-50/90 to-[var(--journal-paper)] px-4 py-3">
        <h2
          id={titleId}
          className="text-lg font-bold text-emerald-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          {title}
        </h2>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          className="inline-flex min-h-11 items-center rounded-md border border-[var(--journal-border)] bg-white px-3 text-sm font-semibold text-slate-700"
        >
          إغلاق
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        {children}
      </div>
    </div>
  );
}
```

`bg-gradient-to-l` is a gradient direction, not a box-edge `left-` utility; do not replace it with `left-0`. Do not add `left-` or `right-` classes.

- [ ] **Step 4: Point `MobileNav` at `MobileSheet`**

At the top of `frontend/src/components/main-nav.tsx`, add this import next to the existing `AgentsNavLink` import:

```ts
import { MobileSheet } from "@/components/mobile-sheet";
```

Replace the entire `function MobileNav` with:

```tsx
function MobileNav() {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useMenuDismiss(open, close, rootRef);

  const flatLinks = [
    primaryNavLink,
    ...navGroups.flatMap((g) => g.items),
    contactNavLink,
  ];

  return (
    <div ref={rootRef} className="relative md:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label="قائمة التنقل"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-11 items-center gap-1 rounded-md border px-3 text-xs font-semibold transition ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "border-[var(--journal-border)] bg-white text-slate-700 active:bg-[var(--journal-accent-soft)]"
        }`}
      >
        القائمة
        <ChevronIcon open={open} />
      </button>
      <MobileSheet open={open} onClose={close} title="القائمة">
        <div id={panelId} className="flex flex-col">
          {isDevMode() ? (
            <div className="border-b border-[var(--journal-border)] px-4 py-3">
              <AgentsNavLink />
            </div>
          ) : null}
          <ul className="py-1">
            {flatLinks.map((item) => (
              <li key={item.href} role="none">
                <Link
                  href={item.href}
                  role="menuitem"
                  onClick={close}
                  className="flex min-h-11 items-center px-4 text-sm text-slate-700 active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </MobileSheet>
    </div>
  );
}
```

Leave `NavDropdown`, `NavTextLink`, `useMenuDismiss`, and `MainNav` as they were at the end of Task 4 (desktop `absolute start-0` stays).

- [ ] **Step 5: Run tests and lint**

Run:

```bash
cd frontend && npm run test:wukala-ux && npm run lint
```

Expected: all `test:wukala-ux` tests PASS. Lint: no errors in `mobile-sheet.tsx` or `main-nav.tsx`.

- [ ] **Step 6: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/src/components/mobile-sheet.tsx frontend/src/components/main-nav.tsx
git commit -m "feat(nav): قائمة الجوال كشاشة كاملة بدل القائمة المنبثقة"
```

---

### Task 6: Signed-in account menu uses `MobileSheet` on small screens

**Files:**
- Modify: `frontend/src/components/auth-header.tsx`
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs`

**Interfaces:**
- Consumes: `MobileSheet` from `@/components/mobile-sheet` with the Task 5 signature `{ open, onClose, title, children }`
- Produces: signed-in mobile UI (`md:hidden`) opens `<MobileSheet title="الحساب">`. Desktop popover stays `hidden md:block` with the existing `absolute end-0 top-full` classes. Guest `تسجيل الدخول` link is unchanged.

- [ ] **Step 1: Add the failing AuthHeader contract**

Append to `frontend/scripts/check-wukala-nondev-ux.mjs`:

```js
test("AuthHeader uses MobileSheet on mobile and keeps the desktop popover", () => {
  const source = readSrc("components/auth-header.tsx");
  assert.match(source, /import \{ MobileSheet \} from "@\/components\/mobile-sheet"/);
  assert.match(source, /<MobileSheet/);
  assert.match(source, /title="الحساب"/);
  assert.match(source, /hidden md:block/);
  assert.match(source, /md:hidden/);
  assert.match(source, /absolute end-0 top-full/);
});
```

- [ ] **Step 2: Run and confirm fail**

Run:

```bash
cd frontend && npm run test:wukala-ux
```

Expected: FAIL — `auth-header.tsx` does not import `MobileSheet`.

- [ ] **Step 3: Split signed-in menu into mobile sheet + desktop popover**

In `frontend/src/components/auth-header.tsx`, add this import after the `readClerkRole` import:

```ts
import { MobileSheet } from "@/components/mobile-sheet";
```

Replace the signed-in `return (` block (the `relative` wrapper that starts after `const isAdmin = …`) with the following. Keep the `!isLoaded` and `!isSignedIn` early returns exactly as they are.

```tsx
  const menuLinks = (
    <>
      <MenuLink href="/maktabi" label="مكتبي" onClick={close} />
      {isAdmin ? (
        <MenuLink href="/admin" label="لوحة الإدارة" onClick={close} />
      ) : null}
      <MenuLink href="/al-idayat" label="إعدادات الحساب" onClick={close} />
    </>
  );

  const signOutButton = (
    <button
      type="button"
      role="menuitem"
      onClick={() => {
        close();
        void signOut({ redirectUrl: "/" });
      }}
      className="flex min-h-11 w-full items-center px-4 text-start text-sm text-slate-600 transition-colors active:bg-rose-50 hover:bg-rose-50 hover:text-rose-800"
    >
      خروج
    </button>
  );

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-11 max-w-[9.5rem] items-center gap-1.5 rounded-md border px-2.5 text-xs font-semibold transition sm:max-w-[12rem] ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "border-[var(--journal-border)] bg-white text-slate-700 active:bg-[var(--journal-accent-soft)] hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
        }`}
      >
        <span className="truncate sm:hidden">حسابي</span>
        <span className="hidden truncate sm:inline">{displayName}</span>
        <ChevronIcon open={open} />
      </button>

      <div className="md:hidden">
        <MobileSheet open={open} onClose={close} title="الحساب">
          <div className="border-b border-[var(--journal-border)] px-4 py-3">
            <p className="truncate text-sm font-semibold text-slate-800">
              {displayName}
            </p>
            {user.primaryEmailAddress?.emailAddress ? (
              <p className="mt-0.5 truncate text-xs text-slate-500">
                {user.primaryEmailAddress.emailAddress}
              </p>
            ) : null}
          </div>
          <div className="py-1">{menuLinks}</div>
          <div className="border-t border-[var(--journal-border)] py-1">
            {signOutButton}
          </div>
        </MobileSheet>
      </div>

      <div
        id={panelId}
        role="menu"
        aria-label="قائمة الحساب"
        className={`absolute end-0 top-full z-50 mt-1.5 hidden w-[min(16rem,calc(100vw-1.5rem))] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md transition-all duration-150 ease-out md:block ${
          open
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        <div className="border-b border-[var(--journal-border)] px-4 py-3">
          <p className="truncate text-sm font-semibold text-slate-800">
            {displayName}
          </p>
          {user.primaryEmailAddress?.emailAddress ? (
            <p className="mt-0.5 truncate text-xs text-slate-500">
              {user.primaryEmailAddress.emailAddress}
            </p>
          ) : null}
        </div>
        <div className="py-1">{menuLinks}</div>
        <div className="border-t border-[var(--journal-border)] py-1">
          {signOutButton}
        </div>
      </div>
    </div>
  );
```

The desktop popover must keep `absolute end-0 top-full` **and** `hidden md:block`. The sheet wrapper must be `md:hidden`. Do not change guest `تسجيل الدخول` copy (that phrase is the site-wide login link, not the wukala Clerk invitation).

- [ ] **Step 4: Run tests and lint**

Run:

```bash
cd frontend && npm run test:wukala-ux && npm run lint
```

Expected: all tests PASS. Lint: no errors in `auth-header.tsx` or `mobile-sheet.tsx`.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/check-wukala-nondev-ux.mjs frontend/src/components/auth-header.tsx
git commit -m "fix(nav): قائمة الحساب على الجوال كشاشة كاملة"
```

---

### Task 7: Lint, desktop + mobile browser verification

**Files:**
- None unless verification finds a regression in the files already listed
- Test: `frontend/scripts/check-wukala-nondev-ux.mjs` (re-run only)

**Interfaces:**
- Consumes: every export produced in Tasks 1–6
- Produces: verified `/wukala` + header behavior at `390×844` and `1280×800`

- [ ] **Step 1: Re-run contracts and lint from a clean frontend cwd**

Run:

```bash
cd frontend && npm run test:wukala-ux && npm run lint
```

Expected: all tests PASS, lint exit 0 (or only pre-existing issues in files this plan did not touch).

- [ ] **Step 2: Start the frontend with Agents visible**

From `frontend/`, ensure `NEXT_PUBLIC_DEV_MODE=true` is in the running env (local `.env` or inline). Then:

```bash
cd frontend && NEXT_PUBLIC_DEV_MODE=true npm run dev
```

Expected: Next.js prints it is ready on `http://localhost:3000`. If `DEV_MODE` was false at last build, stop the server and start again with the variable set — `isDevMode()` is read at build time.

Do **not** commit `.env`.

- [ ] **Step 3: Desktop `1280×800` — page copy and desktop menus**

Open `http://localhost:3000/wukala` at viewport **1280×800**.

Check, as a user would:

1. Eyebrow reads `ربط الوكيل الذكي`. No `Clerk`, no `وضع تطوير`, no `DEV` on the header pill.
2. Header shows the emerald `+ وكلاء` pill in the desktop nav (not inside a hamburger).
3. Hover/click `للمؤلفين` and `عن المجلة`: dropdowns still open under the trigger (`start-0` / visual right in RTL). Do not “fix” them.
4. If signed in, the account popover still opens as a small panel under the name (not a full-screen sheet).
5. On `/wukala`, swipe/click Cursor, ChatGPT, Claude. Every step is Arabic. ChatGPT and Claude badges say `تسجيل دخول التطبيق`. Cursor badge contains `مفتاح ربط`. No `Settings`, `Connectors`, `Developer`, `Integrations`.
6. Click `أنشئ مفتاحك الخاص`: signed-in → `/al-idayat/wukala`; signed-out → `/tawajjuh?next=/al-idayat/wukala`.

- [ ] **Step 4: Mobile `390×844` — distinctive Agents control + full-screen `القائمة`**

Resize to **390×844** (or use device mode). Reload `/`.

Check:

1. The emerald rounded `+ وكلاء` control is visible in the top header cluster **without** opening a menu. It is not a plain text row. It has no `DEV` word.
2. Tap `وكلاء` → `/wukala`. Copy matches Step 3.
3. Tap `القائمة`. A **full-viewport** sheet covers the screen (journal paper + emerald header + `إغلاق`). The panel is **not** a small box sitting to the visual left of the button.
4. The sheet lists the regular nav links. A second `AgentsNavLink` pill appears at the top of the sheet when `isDevMode()` is true. Tapping a link closes the sheet and navigates.
5. Tap `إغلاق` or press Escape: sheet disappears and `document.body` scroll works again.
6. If signed in, tap `حسابي`: another full-viewport sheet titled `الحساب`, not a left popover. Desktop-only popover classes must not be the thing you see at this width.
7. At **320×844**, the header cluster (`وكلاء` + `القائمة` + login/account) must not overflow the viewport. If it does, only shrink `AgentsNavLink` padding further (`px-2`) — do not hide the pill and do not reintroduce `DEV`.

- [ ] **Step 5: Commit verification-only fixes if any, otherwise stop**

If Step 3 or 4 required a code change, run `npm run test:wukala-ux && npm run lint` again, then commit only the files you touched, for example:

```bash
git add frontend/src/components/agents-nav-link.tsx
git commit -m "fix(nav): ضغط زر الوكلاء لعرض 320 بكسل"
```

If nothing changed, do not create an empty commit.

---

## Self-review (author)

**Spec coverage**

| Requirement | Task |
| ----------- | ---- |
| Delete Clerk from user copy; say `تسجيل دخول التطبيق` | 1, 2 |
| All walkthroughs Arabic, including UI chrome | 1, 2 |
| Remove `DEV` from Agents button; keep `DEV_MODE` gate | 3 (badge), 4–5 (gate untouched) |
| Distinctive Agents look visible on mobile header | 4 |
| Mobile menu left-of-button bug → full-screen sheet | 5 (`القائمة`), 6 (account) |
| Desktop menus unchanged | 5, 6, 7 |
| Lint + desktop/mobile browser verification | 2, 5, 6, 7 |

**Placeholder scan:** no TBD/TODO, no “similar to Task N”, no “write tests for the above” without code. Every code step has a full file or a full replacement block.

**Type consistency:** `MobileSheet` is `{ open: boolean; onClose: () => void; title: string; children: ReactNode }` in Tasks 5 and 6. `AgentsNavLink` stays a zero-prop function. `isDevMode()` signature unchanged. `test:wukala-ux` is `node --test scripts/check-wukala-nondev-ux.mjs` from Task 1 onward.
