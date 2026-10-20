# Al-Bayan complete Document2 → Document architecture migration — execution plan

> **Status: PROPOSED EXECUTION PLAN — NOT IMPLEMENTED.** Audit date: **2026-10-20**. No editor deletion, source rename, package upgrade, deployment, or publication has been performed. Each implementation phase must be a separately reviewed PR/MR with the checkboxes below updated from observed evidence. Temporary failures on isolated migration branches are permitted; never merge/publish/deploy incomplete phases.

**BuTeX source-of-truth plan:** [Complete BuTeX legacy editor migration execution plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md). **Earlier naming proposal:** [BuTeX Document2 naming audit](butex-document2-naming.md). This revised plan **supersedes the earlier GUI-only naming boundary**: the owner requires canonical unsuffixed Document names across React, headless TypeScript, CLI/worker, FastAPI routes, backend clients and normal MCP typed commands. It continues to protect the meaning and structure of persisted draft/revision JSON. The earlier proposal cites older 6.1.x package snapshots, which do **not** describe the baseline audited here.

## 1. Executive summary and immutable audit baseline

The first-generation editor deletion is predominantly a **BuTeX source/refactor**. Al-Bayan's observed current **browser** already uses the *second-generation* editor and read-only preview. The migration now includes GUI imports/styles, headless TypeScript types/functions, package-lock/version, CLI/worker binary, HTTP routes, FastAPI backend clients, typed MCP command surface, tests, docs, infrastructure wiring and rollout. The authoritative Al-Bayan FastAPI, headless document worker, Burhan projection and normal MCP typed commands **are explicitly in scope for identifier/route renaming**. Preserve their **behavior**, permission model, mathematical conversion and immutable revision JSON. Do not rewrite stored JSON merely to eliminate a TypeScript, Python or HTTP identifier; audit real serialized version markers as a separate schema decision.

| Repository/baseline | Verified revision on 2026-10-20 | Package contract |
| --- | --- | --- |
| Al-Bayan `develop` | `32e67aba2195ac5940953d1a60b1f64aee31c0bc` | `frontend/package.json` requests `@drghaliasri/butex: ^7.4.2` |
| Al-Bayan `main` | `50cb1255db9d6bb20d60df5dcfe3883168902ef6` | Recently promoted documentation baseline, distinct merge SHA |
| BuTeX `develop` | `be3f564f0f9568d81eb25a2f93bc51b7d1e2b2fc` | `package.json` version **7.4.2** |
| BuTeX `main` | `95a27efb5bc875a3478941ab6fe8cb9a5fa53bc8` | Recent `develop` → `main` docs promotion |

Al-Bayan `frontend/package-lock.json` locks `node_modules/@drghaliasri/butex` to **7.4.2** with an npm registry `resolved` tarball and a recorded `integrity` hash. This is **verified tracked lockfile content**, not evidence that a later npm dist-tag does or does not exist. Re-query the live npm registry via `npm view @drghaliasri/butex version dist-tags --json` before Phase 5/6. On audit, no open migration-specific GitHub PR or GitLab MR was found. Both branches already include recently promoted architecture and proposal docs. Avoid historical local checkouts and claims about old untracked `node_modules`.

The precise current GUI entrypoints in BuTeX `package.json` are `./react-document2` and `./react-document2-preview`; `./react-document` still belongs to the obsolete first editor. The future GUI uses `./react-document` **with a different meaning**, and the dedicated read-only preview is proposed at `./react-document-preview`. The headless `./document2` package becomes `./document`, `Document2Json` becomes `DocumentJson`, the worker CLI becomes `butex-document`, and `/v1/document2/*` becomes `/v1/document/*`, coordinated with Al-Bayan backend/MCP changes.

## 2. Exact current frontend consumer inventory

These imports/consumers were inspected in the current `develop` files or were observed in repository-wide code-search results. Source paths are literal repository paths.

| Component or API | Repository | Generation | Current consumers | Action | Verified justification |
| --- | --- | --- | --- | --- | --- |
| `ButexDocumentEditor2` from `@drghaliasri/butex/react-document2` | Al-Bayan | Current GUI | `frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx` uses `next/dynamic` | MIGRATE to `ButexDocumentEditor` / `react-document` | Article editing already uses Document2; preserve callbacks, figure picker, validity, autosave |
| `ImageAssetRef` from `@drghaliasri/butex/react-document2` | Al-Bayan | Current GUI type | `frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx` | MIGRATE import subpath only | Current asset selection API remains semantically identical |
| `ImageAssetRef` | Al-Bayan | Current GUI type | `frontend/src/components/dashboard/article-assets-panel.tsx` | MIGRATE import subpath only | Asset panel shares the editor picker contract |
| `ImageAssetRef` | Al-Bayan | Current GUI type | `frontend/src/lib/butex-image-assets.ts` | MIGRATE import subpath only | Asset cache/identity conversion must remain unchanged |
| `injectBuTeXDocument2Styles(document)` | Al-Bayan | Current GUI CSS | `frontend/src/lib/butex-mathjax.ts` dynamically imports `react-document2` | MIGRATE to `injectBuTeXDocumentStyles` / `react-document` | Preserve MathJax script startup + BuTeX registration exactly |
| `ButexDocumentPreview` from `react-document2-preview` | Al-Bayan | Current read-only GUI | `frontend/src/components/dashboard/document-frozen-preview.tsx` | MIGRATE **subpath** to `react-document-preview`; keep component name | Dedicated preview must not import/render interactive editor |
| `.butex-document2-widget*`, `--butex-document2-*` | Al-Bayan | Current GUI CSS | `frontend/src/app/globals.css` | MIGRATE selectors/props after comparing actual new BuTeX CSS | Needed for sticky editor chrome, theme, digit picker, Arabic layout |
| `ALBAYAN_BUTEX_THEME_CLASS` | Al-Bayan | Host theme | `frontend/src/lib/butex-theme.ts`, editor/preview | PRESERVE | Host class `albayan-butex-theme` is independent of BuTeX generation; revise comment if helpful |
| `Document2Json`, `Document2Node`, `fromDocumentJson2`, `document2Latex` | Al-Bayan | Headless model | `frontend/src/lib/{butex-latex,butex-validation,draft-autosave}.ts`; `frontend/src/lib/api/articles.ts`; editor page; preview | MIGRATE to `DocumentJson`, `DocumentNode`, `fromDocumentJson`, `documentLatex` and headless `@drghaliasri/butex/document` import | Preserve the *content and semantics* of persisted JSON, conversions, validation and autosave |
| `Document2Json` | Al-Bayan | Headless model | `frontend/src/components/dashboard/{document-frozen-preview,draft-history-dialog}.tsx` and article detail/read pages | MIGRATE type/import only to `DocumentJson` | Frozen revisions continue displaying unchanged historical JSON |
| `@drghaliasri/butex` core | Al-Bayan | Shared MathJax | `frontend/src/lib/butex-mathjax.ts` | PRESERVE | `registerBuTeX`, `BUTEX_TEX_PACKAGE`, `registerBuTeXSvgTextWrapper`, `injectBuTeXStyles` are standalone MathJax integrations |
| `@drghaliasri/butex` version + resolved artifact | Al-Bayan | Package | `frontend/package.json`, `frontend/package-lock.json` | MIGRATE together | A new **major** BuTeX version removes/repurposes public exports |
| CSS selector and preview path source tests | Al-Bayan | Integration tests | `frontend/src/components/dashboard/{article-editor-chrome,history-ui-contract}.test.ts` | MIGRATE expectations, PRESERVE assertions | Tests currently literally match old digit-picker CSS and `react-document2-preview` |
| `/v1/document2/*` and worker request JSON | Al-Bayan | Headless protocol | `backend/app/services/butex_worker_client.py` | MIGRATE URL builders/calls to `/v1/document/*`, update retry/error/health tests and worker deployment | Preserve authorization, payload semantics and math response behavior |
| `MathObject` projection/diagnostics | Al-Bayan | Math protocol | `backend/app/services/{butex_diagnostic_client,burhan_client,burhan_reverse_client}.py` | PRESERVE, verify | Shared BuTeX math extraction must not break its headless worker |
| Typed `Document2` command APIs | Al-Bayan | Backend/MCP | `backend/app/schemas/{document2,draft_command}.py`, `mcp_server/src/albayan_mcp/schemas/document2.py`, `mcp_server/src/albayan_mcp/tools/{drafts,equations}.py` | MIGRATE canonical type/module/tool/command labels to unsuffixed `Document` names; keep validated request semantics and auth | Normal MCP capability discovery and FastAPI/OpenAPI specs must expose final canonical naming |

**Negative finding (scoped):** searched frontend repository source for `@drghaliasri/butex/react-document2` and `@drghaliasri/butex/document`. Current actual browser source consumes only the second-generation GUI and headless model currently exported as `document2`; no first-generation document editor render/import was observed. Historical docs legitimately mention obsolete interfaces and are not current consumers. Re-run strict full-tree `rg` at implementation time; repository code search is not a substitute for a complete imported-package graph.

### CSS, callback and DOM contracts to preserve

The editor page owns `DraftAutosaveController`, authenticated `getArticleDraft`/`putArticleDraft`/`restoreDraftRevision`, revision conflicts, validity, images, `getToken` and `onDocumentJsonChange`. Retain those host behaviors. In `frontend/src/app/globals.css`, replace *only* selectors and vars corresponding to the newly renamed BuTeX widget; preserve `.albayan-butex-theme`, journal tokens, sticky editor offset calculations, RTL, Tailwind reset overrides and three-way numeral-picker restrictions. Compare against the actual final `src/react-document/documentWidgetCss.ts` after BuTeX Phase 3, including styles injected by the **dedicated preview**. Use DOM tests/Playwright to prove selectors still match real elements.

## 3. Verified cross-repository dependency graph

```text
Al-Bayan Next.js article editing route
  → @drghaliasri/butex/react-document2 (now)
    → ButexDocumentEditor2 validated wrapper
      → BuTeX Document2 JSON/model, math adapter, standalone ButexEditor,
        document widget CSS, MathJax island rendering, figure/ref UI
  → @drghaliasri/butex/document2 [Document2Json, validation, LaTeX]
  → Al-Bayan draft-autosave.ts → authenticated FastAPI draft API
  → Al-Bayan image asset list/picker/resolver + host journal theme

Al-Bayan frozen draft/history preview
  → @drghaliasri/butex/react-document2-preview (now)
    → ButexDocumentPreview → Document2 preview model / MathJax SVG
  → same Document2 persisted revision and asset resolver

Normal Al-Bayan MCP → mcp_server API facade / typed commands
  → Al-Bayan FastAPI auth / article_draft_service.py
    → Burhan mathematical conversion / structured MathObject
    → butex_worker_client.py → private /v1/document2/* worker
      → BuTeX src/document2-cli/* + src/document2/*
        → shared math adapter now under src/document/{mathObject,
          mathEditorAdapter,types,normalizeCharImport}.ts
    → immutable articles/{id}/draft/revisions/{revision}/document.json
  → Next.js editor or frozen revision preview → MathJax browser
  → optional separate PDF compiler
```

The four shared BuTeX math modules must be **EXTRACTED, not deleted** before old `src/document/` is retired. See the linked [BuTeX detailed graph](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md#2-verified-dependency-graph). Al-Bayan does **not** need to import internal neutral BuTeX paths; only the new public GUI/preview paths.

### Complete naming cleanup — expanded owner-approved scope (2026-10-20)

This is **not** a frontend-only change. The final architecture must use canonical **Document** names across the entire stack and must not retain old generation-two aliases in active modules, executable names, routes, typed schemas or MCP discovery. The HTTP `/v1` prefix denotes **API version**, not editor generation, and is kept unless independently approved. Mappings are target designs, **not existing implementation**.

| Boundary | Before | After / migration responsibility |
| --- | --- | --- |
| BuTeX headless package | `@drghaliasri/butex/document2` | `@drghaliasri/butex/document`; old first-generation export must be retired first |
| BuTeX headless paths | `src/document2/` | `src/document/` after extracting shared math and deleting obsolete code |
| TS JSON and command names | `Document2Json`, `Document2Node`, `fromDocumentJson2`, `document2Latex`, other `Document2*` | `DocumentJson`, `DocumentNode`, `fromDocumentJson`, `documentLatex` and corresponding unsuffixed commands; update all Al-Bayan imports |
| BuTeX worker source and executable | `src/document2-cli/`, `butex-document2` | `src/document-cli/`, `butex-document` and matching package bin/build/container scripts |
| Worker HTTP API | `/v1/document2/*` | `/v1/document/*`, rename both server routes and Al-Bayan `butex_worker_client.py` URL builders/tests |
| Backend/FastAPI | `backend/app/schemas/document2.py` and active `Document2` schema/route names where found | Canonical `document.py` and `Document` schema/route names; audit actual route declarations/OpenAPI before changing |
| Normal Al-Bayan MCP | `mcp_server/src/albayan_mcp/schemas/document2.py`, typed `Document2` commands and discoverable tool docs | Canonical `document.py`, `Document` commands/tool contracts; end-user-facing normal MCP must verify this (Developer MCP is diagnostic only) |
| Frontend GUI | `react-document2`, `ButexDocumentEditor2`, `react-document2-preview` | `react-document`, `ButexDocumentEditor`, `react-document-preview`; rename style helpers and CSS too |

**Data contract invariant:** *identifier/route renaming is not a mandate to transform existing saved draft JSON*. Freeze canonical fixtures, compare old/new serialization, validate historical immutable revisions and detect any genuine on-wire `document2` discriminator. Such an on-wire change needs a separately approved, backward-data-compatible design; never reinterpret historical articles to make a source-code name look cleaner.

**Deployment invariant:** versioned BuTeX worker and Al-Bayan backend/frontend/MCP must be rolled out as a **compatible unit on development first**, with failing mixed-version states prevented. Do not rely on a worker lagging behind the API rename. Old `/v1/document2/*` must not be a permanent live alias in the final architecture. Production remains unchanged without separate authorization.

## 4. Final public names: agreed boundary with BuTeX

| Shipped today | Proposed final | Al-Bayan action |
| --- | --- | --- |
| `@drghaliasri/butex/react-document2` | `@drghaliasri/butex/react-document` | Update dynamic editor import, ImageAssetRef imports, MathJax style injection |
| `ButexDocumentEditor2` | `ButexDocumentEditor` | Update mounted editor reference; keep props and callbacks |
| `ButexDocumentEditor2Props` / `ButexDocumentEditor2Ref` | `ButexDocumentEditorProps` / `ButexDocumentEditorRef` | Only if types are referenced; current Al-Bayan source observed `ImageAssetRef` |
| `injectBuTeXDocument2Styles` / `DOCUMENT2_WIDGET_CSS` | `injectBuTeXDocumentStyles` / `DOCUMENT_WIDGET_CSS` | MathJax loader and source tests |
| `.butex-document2-widget*` / `--butex-document2-*` | `.butex-document-widget*` / `--butex-document-*` | Host `globals.css` and CSS source tests |
| `@drghaliasri/butex/react-document2-preview` | `@drghaliasri/butex/react-document-preview` | Frozen preview dynamic import (keep `ButexDocumentPreview`) |
| `@drghaliasri/butex/document2`, `Document2Json`, `/v1/document2/*`, `butex-document2` CLI | `@drghaliasri/butex/document`, `DocumentJson`, `/v1/document/*`, `butex-document` CLI | Migrate frontend headless API, Python worker client, MCP schema/typed command names, runtime/config/tests; preserve persisted JSON semantics |
| Standalone `@drghaliasri/butex/react` and main MathJax API | **UNCHANGED** | No change |

**Breaking change:** first-generation `@drghaliasri/butex/document` is removed; the old `react-document` public name is repurposed to the current editor. Do not add transition aliases. Publish a breaking semver-major package only with approval and release gates. Ordinary docs pointing to implemented architecture should not claim migration completed until final code is shipped.

## 5. Al-Bayan tests and CI update inventory

| Test / validation path | Classification | Planned action |
| --- | --- | --- |
| `frontend/src/components/dashboard/article-editor-chrome.test.ts` | Current frontend GUI integration | Rewrite hardcoded `.butex-document2-widget__digit-form-menu` / digit CSS tests to new widget class; preserve header/nav/sticky/locale validations |
| `frontend/src/components/dashboard/history-ui-contract.test.ts` | Current frozen preview integration | Update expected `@drghaliasri/butex/react-document-preview`; keep assertions that preview is lightweight/read-only and not the interactive editor |
| `frontend/src/components/dashboard/authoring-ux-followup.test.ts` | Current authoring UI | Preserve; update only path/name expectations where found |
| `frontend/src/lib/{butex-image-assets,draft-autosave,butex-latex,butex-validation}.test.ts` **where present** | Asset/JSON/revision behavior | Enumerate exact present files; preserve behavior tests and add missing editor callbacks/figure/preview smoke coverage |
| `backend/tests/{test_butex_worker_client,test_butex_math_projection_client,test_draft_equations,test_equation_diagnostics,test_burhan_math_commands,test_draft_revisions}.py` | Headless worker/immutable revision | Preserve; should not need rename; run to prove no behavioral drift |
| `mcp_server/tests/{test_draft_command_schema,test_equation_tools,test_draft_block_projection,test_article_tools}.py` | Normal MCP contracts | Preserve; no schema rename; run before and after integrated dev deployment |
| `.github/workflows/equation-integration-ci.yml` | Actual path-filtered CI | Update affected-file filters **if needed** so GUI import/CSS/lock/test edits trigger relevant frontend checks. Do not invent package scripts |
| `.github/workflows/stripe-donations-ci.yml` | Shared frontend CI | Ensure changed dependency does not break install/typechecking; no change required unless observed |

The verified `.github/workflows/equation-integration-ci.yml` installs Python 3.12 and runs backend/MCP pytest groups. On a changed frontend it executes `npm ci --ignore-scripts --no-audit --no-fund`, scoped `npx vitest run`, `npx tsc --noEmit` and `npm run build`. **Beware:** this workflow is path-filtered; a docs-only PR does not prove frontend integration works. `frontend/package.json` currently defines `npm test` as `vitest run`, `npm run build` as `next build`, `npm run lint` as `next lint` and no `typecheck` script; invoke `npx tsc --noEmit`. Verify `npm run lint` is operational before using it as a release gate rather than pretending it passed.

**Implementation verification commands** (run in a clean checkout once BuTeX final contract available):

```bash
cd frontend
npm ci --ignore-scripts --no-audit --no-fund
npm test
npx tsc --noEmit
npm run build
# npm run lint  # only after verifying the installed Next/ESLint script is functional
# confirm frontend/package-lock.json resolved version and integrity
```

Backend/MCP targeted commands matching the existing workflow (run from repository root with its installed environment):

```bash
PYTHONPATH=backend pytest -q backend/tests/test_butex_worker_client.py backend/tests/test_butex_math_projection_client.py backend/tests/test_draft_equations.py backend/tests/test_equation_diagnostics.py backend/tests/test_draft_revisions.py backend/tests/test_burhan_math_commands.py
PYTHONPATH=mcp_server/src:mcp_server pytest -q mcp_server/tests/test_draft_command_schema.py mcp_server/tests/test_equation_tools.py mcp_server/tests/test_draft_block_projection.py mcp_server/tests/test_article_tools.py
```

Add a focused frontend smoke verifying that dynamic editor and preview imports resolve from **actual npm package exports**, that the wrapper accepts `onValidityChange` and image picker, that editor JSON autosave remains canonical, and that read-only preview does not mount editor UI. Do not delete backend/MCP tests to make migration green.

## 6. Dependency-version and deployment transition

1. Complete BuTeX **Phases 0–4** first on feature branches/MRs, including extraction, removal, GUI promotion, source tests, demo, package exports and final tarball/CI checks. No intermediate build green requirement; do not merge these incompletely into deployment-triggering `develop` or `main`.
2. For a cross-repo integration rehearsal before npm publication, use a controlled locally built tarball or temporary pinned Git/tarball dependency **only in isolated integration branches** if strictly necessary. Do not commit temporary compatibility aliases or cause production/dev shared deployments to pull an incompatible package. Prefer the straightforward published-version transition when the full BuTeX branch is verified.
3. **Phase 5:** human authorizes BuTeX major version/tag/npm release only after final BuTeX gates. Confirm registry propagation and exact tarball integrity. BuTeX GitLab tag triggers its publish pipeline; BuTeX branch `develop`/`main` can trigger **worker deployment**, so keep package / worker compatibility and release order explicit.
4. **Phase 6:** on a new Al-Bayan PR from fresh `develop`, change `frontend/package.json` and `frontend/package-lock.json` in the **same PR**, using `npm install --package-lock-only` after publication, verify resolved+integrity, run `npm ci`. Migrate every identified GUI **and headless** TS symbol, Python worker endpoint, FastAPI and normal MCP typed-command/API name, tests, scripts and documentation.
5. **Phase 7:** coordinate development-only deploy of compatible BuTeX worker and Al-Bayan frontend. Verify origins: `https://dev.albayan-journal.org`, requests to `https://api.dev.albayan-journal.org`. Any production-origin redirect/request is a configuration blocker, not a passed test. Development MCP/browser evidence needed.
6. **Phase 8:** update implemented architecture docs, release notes, external breaking-change guidance and checkboxes; do not merge/deploy until explicitly reviewed.

**Potential pin distinction:** backend currently calls the worker by HTTP URL, not by importing a BuTeX npm React GUI. Verify deployment config/actual worker source revision at Phase 0/7. A separate worker image/version **cannot** be assumed compatible across the breaking HTTP route rename. Coordinate an explicitly tested matching worker/client version pair; do not infer the worker version from `frontend/package-lock.json`. Do not infer its image package version from `frontend/package-lock.json`.

## 7. Tracking checklists — each phase a separate open PR/MR

### Phase 0 — freeze & re-audit both repositories

- [ ] Refresh `develop`/`main` SHAs for BuTeX and Al-Bayan; verify promoted docs and open requests.
- [ ] Verify actual npm dist-tag and worker deployed revision, capture tracked Al-Bayan manifest/lock and package export list.
- [ ] Re-run full-tree references for legacy/current GUI and headless imports, Python schemas, CLI/bin, worker source, `/v1/document2/*` route strings, infrastructure, MCP tools, tests, CSS and packaging; record exact affected files and baseline outcomes.
- [ ] Audit actual frozen/persisted revision JSON and typed command payloads for schema version discriminators: preserve bytes and meaning unless a distinct validated data-migration design is explicitly approved.
- [ ] **Gate:** no unknown consumer is treated as safe for unconditional removal.

### Phase 1 — BuTeX shared-math extraction gate (BuTeX MR; Al-Bayan watches)

- [ ] Verify four math modules extracted from `src/document/` and current Document2/CLI/standalone imports updated.
- [ ] Confirm MathObject import/export, Arabic font normalization, equations and worker diagnostics preserved by tests.
- [ ] **Gate:** Al-Bayan backend diagnostics remain compatible with Document2 worker response.

### Phase 2 — first-generation cleanup gate (BuTeX MR)

- [ ] Remove first-gen GUI, old headless-only model, obsolete demo and exclusively legacy tests only after extraction; free the old `src/document/` and `@drghaliasri/butex/document` names for the maintained headless implementation.
- [ ] Keep the **implementations** under `src/document2/`, `src/document2-cli/`, `src/editor/`, standalone `src/react/` and MathJax intact until they are safely migrated; the first two directories and exported names must ultimately be canonicalized, not deleted.
- [ ] **Gate:** no current source import targets a deleted file; no shared test silently dropped.

### Phase 3 — current GUI promotion gate (BuTeX MR)

- [ ] Ship **full-stack** contract: maintained GUI, preview, scoped CSS, `src/document2/` → `src/document/`, `@drghaliasri/butex/document2` → `/document`, `Document2Json` → `DocumentJson`, associated functions/typed commands, worker executable `butex-document` and `/v1/document/*`; no permanent compatibility aliases.
- [ ] Verify separate validated wrapper and lightweight preview, correct demo/package exported entries.
- [ ] **Gate:** public API table is exact, `Document2` symbols/old binary/old routes are absent from final active names; persisted document structure, math and authorization **behavior** unchanged.

### Phase 4 — BuTeX regression + packaging gate (BuTeX MR)

- [ ] Observe BuTeX `npm ci`, build, typecheck, lint, tests, pack, demo and final GitLab pipeline.
- [ ] Verify renamed worker executable/HTTP routes and commands/math diagnostics, figure/reference persistence, RTL/MathJax in maintained demo; compare serialized JSON fixtures before/after.
- [ ] **Gate:** green final BuTeX state (intermediate failures acceptable only on isolated branches).

### Phase 5 — controlled npm contract publication gate

- [ ] Obtain explicit package release authorization, choose major semver, verify npm peer dependency and immutable tarball.
- [ ] Confirm registry version/integrity and remaining active consumers; release notes describe intentional legacy API break.
- [ ] **Gate:** no implementation PR, npm publish, GitLab tag or deployment triggered by this planning PR alone.

### Phase 6 — Al-Bayan frontend consumer PR

- [ ] Update `frontend/package.json` and `frontend/package-lock.json` together; version exactly matches published artifact.
- [ ] Rename editor imports/JS names in `tahrir/page.tsx`, `ImageAssetRef` consumers, MathJax style injection, read-only preview subpath and `globals.css` selectors **plus** every headless frontend import/type/helper across `butex-latex`, `butex-validation`, `draft-autosave`, article API and frozen revisions.
- [ ] Migrate `backend/app/services/butex_worker_client.py` route mapping to `/v1/document/*`, associated backend schemas/modules/tests/OpenAPI where versioned, and `mcp_server/src/albayan_mcp/schemas/document2.py` and tools to canonical `Document` names. Preserve typed command validation, authorization, Burhan math semantics and immutable revision JSON.
- [ ] Update host style/preview tests and docs; preserve full image/revision/MathJax/auth workflows.
- [ ] Run frontend `npm ci`, `npm test`, `npx tsc --noEmit`, `npm run build`; backend/MCP pytest, worker HTTP contract tests, renamed MCP discovery/schema tests and both repos' CI. Check actual GitHub Actions workflow results.
- [ ] **Gate:** no generation-two naming survives in active frontend/backend/MCP/worker runtime routes or exports, no data corruption, permissions unchanged, all renamed endpoints resolve against matching worker and backend revisions.

### Phase 7 — full development end-to-end (cross-repo validation PRs)

- [ ] Confirm development browser + API origins; load existing draft, type Arabic text, create/reopen mathematical equation, insert figure and reference, validate, autosave, navigate and restore revision.
- [ ] Confirm immutable draft/frozen revision preview uses lightweight `ButexDocumentPreview` and correct new CSS; MathJax SVG and RTL/digit form observed.
- [ ] Invoke the **normal Al-Bayan MCP** with a supported canonical English LaTeX typed **Document** command on an authorized development draft; verify tool discovery uses final names and follow source→Burhan MathObject→**renamed `/v1/document/*` worker**→stored JSON→renamed GUI roundtrip.
- [ ] Use **Developer MCP** for intermediate diagnostics, Playwright MCP for actual DOM/network/equation rendering, and optional development PDF compilation for visual consistency.
- [ ] Verify development FastAPI OpenAPI/worker route enumeration exposes `/v1/document/*` and no obsolete `/v1/document2/*`, CLI responds to `butex-document`, retained historical revisions load without rewrite.
- [ ] **Gate:** all pipeline stages independently evidenced. Unit tests alone are insufficient. Do not modify production data or services.

### Phase 8 — final docs + release readiness (docs PRs)

- [ ] Update implemented (not merely proposed) BuTeX/Al-Bayan docs, consumer examples, CSS/public symbols, package/headless types, FastAPI/MCP endpoints, worker/CLI runbooks and version notes; remove active Document2/`document2` generation labels. Migration/historical audit evidence may quote old identifiers as before-state facts.
- [ ] Verify final CI checks in both repos and stage-specific approvals; link each phase PR/MR and confirm checkboxes.
- [ ] **Gate:** no release/deploy without explicit authorization and complete cross-repo pass.

## 8. Cross-repo acceptance matrix

| Scenario | Where observed | Accept only if |
| --- | --- | --- |
| Package version + exports | npm registry, installed `node_modules`, manifest+lock | `react-document`/`react-document-preview` resolve new API, removed versioned GUI does not; `document2` unchanged |
| Article editing and save | Browser/Next and FastAPI | Validated wrapper, image callback and `onDocumentJsonChange` work, revision conflict handling intact |
| Figures/captions/references | Current Document2 tests, preview, browser | Asset identifiers, captions, labels, bibliographic references survive roundtrip |
| Mathematics | Normal MCP, Burhan, Document2 worker, GUI | Canonical LaTeX is converted, stored MathObject reopens as editable (or reports real unsupported reason), SVG rendered |
| Arabic UX | Browser DOM + screenshot + CSS tests | Correct RTL, themes, numeral chooser, MathJax display, mobile toolbar |
| Frozen/history preview | Dedicated dynamic preview + revision storage | Same selected immutable revision, no editor chrome, correct styling/image assets |
| Security/identity | FastAPI/MCP tests | Auth and scoped draft changes preserved; no redirect to production |
| Optional compiled output | Development compiler if configured | Same structured equations/refs/assets rendered consistently; no false claim if compiler unavailable |

## 9. Risks, mitigations, recovery and hard release gates

| Risk | Prevention and verification | Release blocker |
| --- | --- | --- |
| Shared `MathObject` adapter deleted with first-generation model | BuTeX extraction/test gate before deletion; worker diagnostics | Any converter import or equation roundtrip failure |
| Transitive imports or worker package version hidden | Source graph, worker deployment revision and HTTP health verification | Unknown dependency classified DELETE or incompatible worker |
| Figure/reference/caption behavior changes | Existing Document2, Al-Bayan asset and revision tests plus dev browser | Missing asset/label/immutable revision |
| MathJax/RTL or host CSS selector mismatch | Compare final widget CSS, update `globals.css` and frontend contract tests, Playwright | SVG/RTL/preview visually wrong |
| Preview/editor export confusion | Separate preview package entry, test no editor mount | Frozen preview interactive or blocked |
| npm version / lockfile / integrity drift | Major-release gate, `npm install --package-lock-only`, `npm ci` | Lock differs from published artifact |
| Tests falsely green from deletion | Retain shared/headless tests, strengthen source-path assertions | Required regressions removed or path assumptions stale |
| Worker/MCP interface partially renamed | Coordinate explicit `document` model/HTTP route/typed schema migration across BuTeX and Al-Bayan; validate new OpenAPI/MCP discovery and worker tests | Mismatched endpoint, stale tooling or backend/MCP/immutable revision regression |
| Frontend/development service skew | Coordinate versioned rollout; test dev origins and HTTP outputs | Mixed incompatible artifacts |
| Existing third-party production users of removed legacy GUI | Major semver + documented breaking behavior, do not deploy prod | Missing explicit authorization or notice |

**Recovery:** Abandon/revert isolated phase branches; maintain current known-good `develop` until all final gates. If a new npm artifact has been published, do not rewrite that published tarball; pin Al-Bayan to its prior working version/lock and repair in new commits. Roll back development frontend/worker independently only after verifying current API compatibility; never mutate historical article revisions, authentication or production data to compensate for a GUI rename.

## 10. Definition of done

- [ ] BuTeX's [complete source-preservation, cleanup and GUI rename plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md) completed and final package tested/released with approval.
- [ ] Every active Al-Bayan editor, asset, style, frozen preview, test and documentation reference uses the final public GUI names; standalone equation/MathJax behavior survives.
- [ ] `frontend/package.json` and `frontend/package-lock.json` agree with a verified published release.
- [ ] Active headless `@drghaliasri/butex/document`, `DocumentJson`, `butex-document`, `/v1/document/*`, backend typed **Document** commands and normal MCP tool/schema names are canonical and unsuffixed; immutable draft/revision **JSON contents**, authorization/security and mathematical semantics remain unchanged.
- [ ] Frontend, backend, MCP, BuTeX CI and **development browser/MCP end-to-end evidence** all pass.
- [ ] Each phase executed as individually reviewable requests with progress checkboxes; every future merge, publish and deployment approved separately.

### Evidence provenance and limitations

Verified `develop` sources include Al-Bayan `frontend/package.json`, `frontend/package-lock.json`, editor page, `butex-mathjax.ts`, `butex-image-assets.ts`, frozen preview, `globals.css`, `article-editor-chrome.test.ts`, `history-ui-contract.test.ts`, `backend/app/services/butex_worker_client.py`, `article_draft_service.py`, `docs/architecture/mcp.md`, `.github/workflows/equation-integration-ci.yml`; cross-referenced BuTeX `src/document2/mathBridge.ts`, `src/document2/types.ts`, `src/react-document2/index.ts`, `tsup.config.ts` and the package manifest. Some repository-wide search hits identify further consumers; Phase 0 requires a full re-run of a real checkout symbol/import graph. **No tests, runtime release, MCP diagnostic, Playwright browser session or CI pipeline were executed for this documentation-only task.** No claims of a passing integration test are made.
