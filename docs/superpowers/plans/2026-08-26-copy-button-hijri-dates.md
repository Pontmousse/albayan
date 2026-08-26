# Copy Button + Hijri Dates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every text “نسخ” control with one icon copy button that animates to a check after a successful copy, and make every user-visible date in the frontend Umm al-Qura Hijri via a single helper.

**Architecture:** A shared client `CopyButton` owns clipboard write, the clipboard/check SVG, and the copied animation. Date display funnels through `formatDate` / `formatDateTime` / `formatHijriYear` in `frontend/src/lib/format-date.ts` using `Intl.DateTimeFormat("ar-SA-u-ca-islamic-umalqura")`. Call sites keep passing ISO strings; `<time dateTime>` stays Gregorian ISO. AGENTS.md records both as design constraints for future work.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind 4 (logical properties), Node 22 `Intl` + `node --test`. No new npm packages. No icon library.

## Feasibility (Hijri)

`islamic-umalqura` is **not used anywhere today**. Display dates go through Gregorian `Intl.DateTimeFormat("ar")` in [`frontend/src/lib/format-date.ts`](frontend/src/lib/format-date.ts). One extra Gregorian formatter lives in [`frontend/src/components/settings/security-form.tsx`](frontend/src/components/settings/security-form.tsx). The footer copyright is a hardcoded `© ١٤٤٧ هـ`. Backend invitation emails use `strftime("%Y-%m-%d %H:%M UTC")` (Gregorian) — **out of scope** (not UI).

Node 22 in this environment already supports the calendar. Sample for `2026-08-26`:

| locale | calendar | example |
|--------|----------|---------|
| `ar-SA-u-ca-islamic-umalqura` | `islamic-umalqura` | `١٣ ربيع الأول ١٤٤٨ هـ` |
| `ar` (current) | `gregory` | `26 أغسطس 2026` |

**Locked display rule:** user-visible dates are Umm al-Qura Hijri with Arabic-Indic digits (`ar-SA`). Machine-readable `dateTime` / API payloads stay ISO Gregorian. Do not dual-print Gregorian next to Hijri unless a later request asks for it.

## Global Constraints

- No new npm dependencies (no Lucide/Heroicons). Inline SVG only.
- Copy control is **icon-only** (clipboard → check). Visible label text like `نسخ المفتاح` / `نسخ TeX` is removed from the button. `aria-label` is `نسخ` or `تم النسخ`.
- Copied state lasts ~1.6s then returns to clipboard. Respect `prefers-reduced-motion`.
- Root is `lang="ar"` `dir="rtl"`. New Tailwind uses logical properties (`ms-`, `me-`, `start`, `end`).
- Displayed dates: `ar-SA-u-ca-islamic-umalqura` only, via `format-date.ts`. Do not call `Intl.DateTimeFormat` for UI dates outside that file.
- `<time dateTime={iso}>` remains the ISO Gregorian instant.
- Backend email timestamps stay UTC Gregorian.
- Do not add Jest/Vitest/Playwright. Contracts: `node --test` + `npm run lint` + browser check of the token reveal modal and one dashboard date.
- Do not edit the plan file itself during execution.

## File map

| File | Responsibility |
| ---- | -------------- |
| Create: `frontend/src/components/ui/copy-button.tsx` | Shared icon copy button + animation. |
| Modify: `frontend/src/app/globals.css` | `.copy-button` copied keyframes. |
| Modify: `frontend/src/components/settings/agent-tokens-panel.tsx` | Icon copy on the reveal `<pre>`; drop text copy button and local `copied` state. |
| Modify: `frontend/src/components/wukala/chatgpt-detailed-guide.tsx` | `CopyValue` uses `CopyButton`. |
| Modify: `frontend/src/components/dashboard/document-json-dev-dialog.tsx` | Dev JSON copy uses `CopyButton`. |
| Modify: `frontend/src/components/dashboard/exported-tex-dev-panel.tsx` | Dev TeX copy uses `CopyButton`. |
| Modify: `frontend/src/lib/format-date.ts` | Hijri `formatDate`, `formatDateTime`, `formatHijriYear`. |
| Modify: `frontend/src/components/settings/security-form.tsx` | Session timestamps use `formatDateTime`. |
| Modify: `frontend/src/components/site-footer.tsx` | Copyright year from `formatHijriYear`. |
| Modify: `AGENTS.md` | Copy-button + Hijri constraints. |
| Create: `frontend/scripts/check-copy-hijri.mjs` | Source + Intl contracts. |
| Modify: `frontend/package.json` | `test:copy-hijri` script. |
| Modify: `frontend/src/components/journal/article-card.tsx` | No logic change; `formatDate` output becomes Hijri automatically. Same for all other `formatDate` imports. |

**Do not modify:** backend email `strftime`, database columns, API ISO fields, MCP docs calendars.

---

### Task 1: Shared CopyButton

**Files:**
- Create: `frontend/src/components/ui/copy-button.tsx`
- Modify: `frontend/src/app/globals.css` (append after existing `@media (prefers-reduced-motion: reduce)` copy-related rules, near other UI utilities)
- Test: `frontend/scripts/check-copy-hijri.mjs` (created in this task with the CopyButton assertions only; Hijri assertions added in Task 3)

**Interfaces:**
- Consumes: `navigator.clipboard.writeText`
- Produces: `CopyButton({ value, ariaLabel?, className? }: { value: string; ariaLabel?: string; className?: string })`

- [ ] **Step 1: Write the failing source contract**

Create `frontend/scripts/check-copy-hijri.mjs`:

```javascript
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: FAIL — file `copy-button.tsx` does not exist (`ENOENT`).

- [ ] **Step 3: Write CopyButton + CSS**

`frontend/src/components/ui/copy-button.tsx`:

```tsx
"use client";

import { useState } from "react";

export function CopyButton({
  value,
  ariaLabel = "نسخ",
  className = "",
}: {
  value: string;
  ariaLabel?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      onClick={() => void handleCopy()}
      aria-label={copied ? "تم النسخ" : ariaLabel}
      data-copied={copied ? "true" : "false"}
      className={`copy-button inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] ${className}`}
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {copied ? (
          <path d="M5 13l4 4L19 7" />
        ) : (
          <>
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </>
        )}
      </svg>
    </button>
  );
}
```

Append to `frontend/src/app/globals.css`:

```css
.copy-button[data-copied="true"] {
  border-color: color-mix(in srgb, var(--journal-accent) 55%, var(--journal-border));
  color: var(--journal-accent-strong);
  background: var(--journal-accent-soft);
  animation: copy-pop 420ms var(--motion-ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}

@keyframes copy-pop {
  0% {
    scale: 1;
  }
  40% {
    scale: 1.12;
  }
  100% {
    scale: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .copy-button[data-copied="true"] {
    animation: none;
  }
}
```

- [ ] **Step 4: Run the contract test**

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/copy-button.tsx frontend/src/app/globals.css frontend/scripts/check-copy-hijri.mjs
git commit -m "feat(ui): add icon CopyButton with copied pop animation"
```

---

### Task 2: Wire CopyButton across copy sites

**Files:**
- Modify: `frontend/src/components/settings/agent-tokens-panel.tsx`
- Modify: `frontend/src/components/wukala/chatgpt-detailed-guide.tsx`
- Modify: `frontend/src/components/dashboard/document-json-dev-dialog.tsx`
- Modify: `frontend/src/components/dashboard/exported-tex-dev-panel.tsx`
- Test: `frontend/scripts/check-copy-hijri.mjs`

**Interfaces:**
- Consumes: `CopyButton` from `@/components/ui/copy-button`
- Produces: no new exports

- [ ] **Step 1: Extend the failing contract**

Add to `frontend/scripts/check-copy-hijri.mjs`:

```javascript
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
```

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: FAIL — sites still use text buttons.

- [ ] **Step 2: Token reveal modal**

In `agent-tokens-panel.tsx`:
- Import `CopyButton`.
- Delete `copied` state, `handleCopy`, and the `نسخ المفتاح` button.
- Keep the `تمّ` dismiss button.
- Put the icon on the key itself:

```tsx
<div className="relative mt-4">
  <pre
    dir="ltr"
    className="overflow-x-auto rounded-lg border border-[var(--journal-border)] bg-slate-950 p-3 pe-12 text-start text-xs text-emerald-100"
  >
    {revealedToken}
  </pre>
  <CopyButton
    value={revealedToken}
    className="absolute end-2 top-2 border-white/20 bg-slate-900 text-emerald-100 hover:border-emerald-300 hover:text-white"
  />
</div>
```

(`end-2` is logical; in LTR `pre` the button still sits on the inline-end of the box.)

- [ ] **Step 3: ChatGPT CopyValue**

Replace the text `<button>` in `CopyValue` with:

```tsx
<CopyButton value={step.copyValue} ariaLabel={step.copyLabel ?? "نسخ"} />
```

Remove local `copied` / `handleCopy` from `CopyValue`. Keep the `<code>` display.

- [ ] **Step 4: Dev JSON + TeX panels**

`document-json-dev-dialog.tsx` and `exported-tex-dev-panel.tsx`: replace the labelled copy `<button>` with `<CopyButton value={prettyText} />` / `<CopyButton value={tex} />`. Remove `copied` state and `handleCopy`. Keep expand/collapse/close.

- [ ] **Step 5: Run contracts + lint**

```bash
node --test frontend/scripts/check-copy-hijri.mjs
cd frontend && npm run lint
```

Expected: PASS / no ESLint errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/settings/agent-tokens-panel.tsx \
  frontend/src/components/wukala/chatgpt-detailed-guide.tsx \
  frontend/src/components/dashboard/document-json-dev-dialog.tsx \
  frontend/src/components/dashboard/exported-tex-dev-panel.tsx \
  frontend/scripts/check-copy-hijri.mjs
git commit -m "feat(ui): use icon CopyButton on token reveal and other copy sites"
```

---

### Task 3: Hijri formatDate helpers

**Files:**
- Modify: `frontend/src/lib/format-date.ts`
- Test: `frontend/scripts/check-copy-hijri.mjs`

**Interfaces:**
- Consumes: ISO date strings / `Date`
- Produces:
  - `formatDate(iso: string): string`
  - `formatDateTime(value: Date): string`
  - `formatHijriYear(value?: Date): string`

- [ ] **Step 1: Write the failing Intl contract**

Append:

```javascript
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
```

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: FAIL on `formatDateTime` / locale string in `format-date.ts`. The frozen-date Intl assertion should already PASS (proves engine support).

- [ ] **Step 2: Implement helpers**

Replace `frontend/src/lib/format-date.ts` with:

```ts
const HIJRI_LOCALE = "ar-SA-u-ca-islamic-umalqura";

const dateFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  year: "numeric",
  month: "long",
  day: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  dateStyle: "medium",
  timeStyle: "short",
});

const yearFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  year: "numeric",
});

export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

export function formatDateTime(value: Date): string {
  return dateTimeFormatter.format(value);
}

export function formatHijriYear(value: Date = new Date()): string {
  return yearFormatter.format(value);
}
```

- [ ] **Step 3: Run tests**

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/format-date.ts frontend/scripts/check-copy-hijri.mjs
git commit -m "feat(ui): format visible dates with Umm al-Qura Hijri"
```

---

### Task 4: Remaining Gregorian UI + constraints

**Files:**
- Modify: `frontend/src/components/settings/security-form.tsx`
- Modify: `frontend/src/components/site-footer.tsx`
- Modify: `AGENTS.md`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: `formatDateTime`, `formatHijriYear`
- Produces: none

- [ ] **Step 1: Failing contract for leftover Gregorian UI formatters**

Append:

```javascript
test("no UI file besides format-date.ts constructs DateTimeFormat", () => {
  const { readdirSync, statSync } = await import("node:fs");
  // Implemented as a grep in the test file via reading known leftovers:
});
```

Do **not** use that incomplete stub. Use this instead:

```javascript
test("security-form and site-footer do not use Gregorian Intl", () => {
  const security = readSrc("components/settings/security-form.tsx");
  const footer = readSrc("components/site-footer.tsx");
  assert.equal(security.includes("Intl.DateTimeFormat"), false);
  assert.match(security, /formatDateTime/);
  assert.equal(footer.includes("١٤٤٧"), false);
  assert.match(footer, /formatHijriYear/);
});
```

Run: `node --test frontend/scripts/check-copy-hijri.mjs`

Expected: FAIL

- [ ] **Step 2: security-form**

Delete `formatSessionDate`. Import `formatDateTime` from `@/lib/format-date`. Replace calls `formatSessionDate(session.lastActiveAt)` with `formatDateTime(session.lastActiveAt)` (keep the `if (!value) return "—"` guard inline or a one-liner at the call site).

- [ ] **Step 3: footer copyright**

`site-footer.tsx` is a server component — `formatHijriYear` is pure and has no `"use client"`, so it is safe to import.

```tsx
import { formatHijriYear } from "@/lib/format-date";
```

```tsx
<p>© {formatHijriYear()} مجلة البيان. جميع الحقوق محفوظة.</p>
```

(`formatHijriYear()` already includes `هـ` from Intl, e.g. `١٤٤٨ هـ`.)

- [ ] **Step 4: AGENTS.md — add after the العربية section**

```markdown
## التواريخ الظاهرة

- كل تاريخ يظهر للمستخدم في الواجهة هجري أم القرى عبر `formatDate` / `formatDateTime` / `formatHijriYear` في `frontend/src/lib/format-date.ts` (`ar-SA-u-ca-islamic-umalqura`).
- لا تستدعِ `Intl.DateTimeFormat` لتواريخ الواجهة خارج هذا الملف.
- أبقِ `dateTime` على `<time>` (وأي حمولة API) بالميلادي ISO.

## النسخ إلى الحافظة

- أزرار النسخ أيقونة الحافظة المشتركة `CopyButton` في `frontend/src/components/ui/copy-button.tsx` — بلا نص «نسخ» ظاهر.
```

- [ ] **Step 5: package.json**

Add `"test:copy-hijri": "node --test scripts/check-copy-hijri.mjs"` next to `test:wukala-ux`.

- [ ] **Step 6: Run full frontend checks**

```bash
cd frontend && npm run test:copy-hijri && npm run test:wukala-ux && npm run lint
```

Expected: all PASS.

- [ ] **Step 7: Browser**

- Signed-in `/al-idayat/wukala`: create a key → reveal modal shows clipboard on the key; click → icon becomes a check and pops; click again after reset still copies.
- `/wukala` ChatGPT detailed guide copy icons behave the same.
- Any `formatDate` surface (e.g. `/maktabi` if signed in, or article cards) shows `… هـ`, not `أغسطس 2026`.
- Footer year is current Umm al-Qura year, not hardcoded ١٤٤٧.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/settings/security-form.tsx \
  frontend/src/components/site-footer.tsx \
  AGENTS.md frontend/package.json frontend/scripts/check-copy-hijri.mjs
git commit -m "feat(ui): Hijri dates as the display calendar; document copy and date rules"
```

---

## Out of scope

- Dual Hijri + Gregorian strings in the same label
- Backend / email `strftime` UTC
- Changing stored timestamps
- New date-picker widgets
