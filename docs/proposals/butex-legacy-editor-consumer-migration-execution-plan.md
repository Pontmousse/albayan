# Al-Bayan complete Document2 → Document architecture migration — execution plan

> **Status: PROPOSED EXECUTION PLAN — NOT IMPLEMENTED.** Audit date: **2026-10-20**; synchronized eight-round plan updated **2026-10-21**. No editor deletion, source rename, package upgrade, deployment, or publication has been performed. These *planning* requests contain the same frozen-v1 acceptance specification; after their review/merge, use **one long-lived implementation PR plus one long-lived implementation MR** with phase-labeled commits, shared gates, and a final Round-7 stress run. Intermediate development breakage is explicitly permitted; no backward-compatibility shims are required.

**BuTeX source-of-truth plan:** [Complete BuTeX legacy editor migration execution plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md). **Earlier naming proposal:** [BuTeX Document2 naming audit](butex-document2-naming.md). This revised plan **supersedes the earlier GUI-only naming boundary**: the owner requires canonical unsuffixed Document names across React, headless TypeScript, CLI/worker, FastAPI routes, backend clients and normal MCP typed commands. It continues to protect the meaning and structure of persisted draft/revision JSON. The earlier proposal cites older 6.1.x package snapshots, which do **not** describe the baseline audited here.

## 1. Executive summary and immutable audit baseline

The first-generation editor deletion and canonical headless promotion require a **BuTeX source/refactor** plus coordinated **Al-Bayan backend, MCP and frontend integration**. Al-Bayan's observed current **browser** already uses the *second-generation* editor and read-only preview. The migration now includes GUI imports/styles, headless TypeScript types/functions, package-lock/version, CLI/worker binary, HTTP routes, FastAPI backend clients, typed MCP command surface, tests, docs, infrastructure wiring and rollout. The authoritative Al-Bayan FastAPI, headless document worker, Burhan projection and normal MCP typed commands **are explicitly in scope for identifier/route renaming**. Preserve their **behavior**, permission model, mathematical conversion and immutable revision JSON. Do not rewrite stored JSON merely to eliminate a TypeScript, Python or HTTP identifier; audit real serialized version markers as a separate schema decision.

| Repository/baseline | Verified revision on 2026-10-20 | Package contract |
| --- | --- | --- |
| Al-Bayan `develop` | `32e67aba2195ac5940953d1a60b1f64aee31c0bc` | `frontend/package.json` requests `@drghaliasri/butex: ^7.4.2` |
| Al-Bayan `main` | `50cb1255db9d6bb20d60df5dcfe3883168902ef6` | Recently promoted documentation baseline, distinct merge SHA |
| BuTeX `develop` | `be3f564f0f9568d81eb25a2f93bc51b7d1e2b2fc` | `package.json` version **7.4.2** |
| BuTeX `main` | `95a27efb5bc875a3478941ab6fe8cb9a5fa53bc8` | Recent `develop` → `main` docs promotion |

Al-Bayan `frontend/package-lock.json` locks `node_modules/@drghaliasri/butex` to **7.4.2** with an npm registry `resolved` tarball and a recorded `integrity` hash. This is **verified tracked lockfile content**, not evidence that a later npm dist-tag does or does not exist. Re-query the live npm registry via `npm view @drghaliasri/butex version dist-tags --json` before the Round 7 authorized release decision. On audit, no open migration-specific GitHub PR or GitLab MR was found. Both branches already include recently promoted architecture and proposal docs. Avoid historical local checkouts and claims about old untracked `node_modules`.

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

The editor page owns `DraftAutosaveController`, authenticated `getArticleDraft`/`putArticleDraft`/`restoreDraftRevision`, revision conflicts, validity, images, `getToken` and `onDocumentJsonChange`. Retain those host behaviors. In `frontend/src/app/globals.css`, replace *only* selectors and vars corresponding to the newly renamed BuTeX widget; preserve `.albayan-butex-theme`, journal tokens, sticky editor offset calculations, RTL, Tailwind reset overrides and three-way numeral-picker restrictions. Compare against the actual final `src/react-document/documentWidgetCss.ts` after BuTeX Round 5, including styles injected by the **dedicated preview**. Use DOM tests/Playwright to prove selectors still match real elements.

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
| `backend/tests/{test_butex_worker_client,test_butex_math_projection_client,test_draft_equations,test_equation_diagnostics,test_burhan_math_commands,test_draft_revisions}.py` | Headless worker/immutable revision | Preserve the tests; **update route and typed command assertions** to canonical names, and run to prove no behavioral drift |
| `mcp_server/tests/{test_draft_command_schema,test_equation_tools,test_draft_block_projection,test_article_tools}.py` | Normal MCP contracts | Preserve and migrate tool/schema name assertions; run before and after integrated dev deployment |
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

## 6. Synchronized cross-repository execution contract (Rounds 0–7)

**Authoritative Phase 0 acceptance oracle (identical file in both repositories):** [Frozen Document migration acceptance v1](document-migration-frozen-acceptance-v1.md). The owner reviews and freezes this **before implementation**; save a SHA-256 of each copy and verify byte-for-byte equality. After freeze, **do not change either copy to accommodate failures**. Implement/test against it through migration and ask the AI agent to run the **entire specified acceptance/stress suite only in Round 7**, after the migration implementation is complete. A defect in the specification requires an explicitly reviewed, versioned addendum, never an in-place edit. This documentation PR/MR authors the contract; Phase 0 is not complete until it is reviewed and formally frozen.

**Eight planned AI-agent work rounds, exactly synchronized across the two repositories:**

| Round | Shared objective | Al-Bayan responsibility | BuTeX responsibility | Shared exit rule |
| --- | --- | --- | --- | --- |
| **0** | Author/review/freeze acceptance specification; align planning baselines | Mirror the frozen document; record agreed naming and final assertions | Mirror the **same bytes** and agree on worker/package invariants | Both confirm specification hash, shared phase ledger and owner approval |
| **1** | Build the migration diagnostic harness **before editing legacy runtime** | Design/implement/test Developer MCP `dev_document_contract_snapshot`, `dev_document_inspect`, `dev_document_compare`, named suites, fixture report schema and safe diagnostic backend endpoints | Supply real current worker commands/types, test fixtures and any narrow stateless adapter required for diagnostics | Harness contracts/tests pass; old-implementation baseline and build provenance captured |
| **2** | Full dependency and persistence audit, then extract live shared math | Classify all frontend/backend/MCP/deploy references and immutable revision data; pin baseline consumers | Regenerate import graph; mark DELETE/PRESERVE/EXTRACT/MIGRATE; extract four shared `src/document/` math modules; preserve standalone math | No unknown inbound dependency on planned deletions; extraction verified |
| **3** | Remove first-generation BuTeX editor/model and free canonical names | Track integration impact and update affected test inventories as needed; no runtime compatibility requirement | Remove classified obsolete GUI/model/demo/legacy-only tests; preserve current implementation and shared math | Legacy code removed without losing shared functionality; interim builds may fail |
| **4** | Promote maintained headless `Document` and worker/CLI HTTP interface | Update backend worker client endpoints/types against candidate worker; add matching route/contract tests | Move current headless `src/document2/` to `src/document/`, `src/document2-cli/` to `src/document-cli/`; canonical worker/bin/`/v1/document/*`/types/exports | Canonical stateless worker operations and backend client agree in isolated integration tests |
| **5** | Promote maintained React GUI/preview and Al-Bayan frontend consumer | Replace GUI/headless imports, CSS/asset/preview/types and frontend tests; consume local candidate BuTeX tarball without npm publishing | Promote `react-document2`/preview to `react-document`/preview; rename CSS/injector/demo; produce consumable tested tarball | Candidate GUI/editor/preview and frontend integrate locally; no permanent aliases |
| **6** | Finish Al-Bayan FastAPI + normal MCP renaming, CI, candidate integration | Canonical typed Document schemas/tools/commands/backend tests, CI, security and revision invariants; coordinate **development-only** candidate integration | Finish full source tests, CLI/worker contracts, packaging, candidate artifact, final required CI | Full candidate cross-repo build/contract gates pass; ready for **final** acceptance, not released |
| **7** | Run **frozen** complete validation and stress; prepare release decisions | AI agent runs Developer MCP test matrix, separate normal MCP + Playwright, authorized dev compile/revision tests, evidence report | Verify candidate worker/package tests, old-name absence, baseline/candidate equivalence, CI and package provenance | Every mandatory frozen test passed in both ledgers; blockers are not checked off; human authorizes any later merge/tag/npm/deployment |

**Checkbox synchronization:** these rows are the **same numbered work rounds and shared gates in both documents**. Each repository contains local subtasks below, but the **round-level checkbox** may be checked in **both places at once only when all cross-repo requirements for that round are evidenced**. A local no-change task is marked `N/A — verified`, not silently marked completed. A BuTeX-only operation does not automatically complete an Al-Bayan phase, or vice versa. Maintain a small evidence ledger per round: BuTeX commit, Al-Bayan commit, Developer MCP report/CI links, failed/partial gaps and human approval.

**Branch/PR/MR strategy:** Merge/review these **documentation-only** planning PR #236 and MR !66 first when approved. Subsequently create **one long-lived implementation GitHub PR in Al-Bayan and one long-lived implementation GitLab MR in BuTeX**, both based on a fresh `develop`, and **keep adding phase-labeled commits to those same two open requests for Rounds 1–7**. Do **not** open one PR/MR per round. Review the commits/checkpoints and update both ledgers; do not merge either implementation request until final integration and explicit human approval. Recording checkpoints as commits does not mean intermediate CI must be green.

**Intermediate-state policy:** This is an intentional breaking refactor in a development-only workflow. It is acceptable for the unmerged implementation branches, cross-repo candidate combinations, and **explicitly authorized development deployments** to be temporarily broken while different layers are migrated. Do not add compatibility aliases, parallel `document2` routes or shims merely to make intermediate rounds pass; there is **no backward-compatibility requirement during migration**. There **is** a final behavioral compatibility requirement for preserved JSON, math, authorization and revision semantics. Report temporary failures as `expected_intermediate` with evidence rather than pretending they passed. Never deploy these states to production.

**Development infrastructure:** Al-Bayan's [observed Railway environment inventory](../development/railway-infrastructure.md) states `develop` feeds persistent Railway `development` and `main` feeds `production`; do not assume unmerged PR source is deployed automatically. The BuTeX worker is independently built/deployed and may not follow the same source revision. For live candidate tests, use an explicitly authorized isolated local/preview development target or coordinated **development-only** deployment and attest the exact source revisions. Avoid an accidental production rollout, and do not infer health from a successful Railway deployment status.

**Tests versus the frozen oracle:** Rounds 1–6 should run *focused diagnostics and existing/added CI tests* to guide repairs; this does **not** consume or redefine the frozen Round-7 full acceptance decision. The `dev_document_*` suite is a new **Developer MCP** domain, separate from the normal MCP's public authoring tools. Dev MCP must remain bounded/authenticated and nonpersistent; no arbitrary POST, shell, database, deployment, or production authority. Tests requiring a real browser must use Playwright MCP separately; tests of the public typed authoring path must use the normal MCP separately. Agent access to both repositories does not collapse these observation boundaries.

### Frozen-spec provenance and eight-round agent handoff protocol

**Current planning-branch evidence (2026-10-21):** `docs/proposals/document-migration-frozen-acceptance-v1.md` is already committed in **both** planning branches, with **66 numbered acceptance cases** and a separate final stress procedure. The two copies were checked byte-for-byte and had the same Git blob SHA **`86f701828f61704710f12dda5790697118f97c47`**. This Git blob ID is an identity check, **not** the SHA-256 freeze record and **not** owner approval; record and cross-check the actual SHA-256 of both files as a Round-0 deliverable. The v1 test specification must **not** be edited during Rounds 1–7, even if an agent discovers failed tests or inconvenient expectations. Place progress, implementation corrections, fixture outputs, new tests and proposed clarifications **outside** v1; exceptional specification errors require a separately approved **v2/addendum** and explicit acceptance-decision record.

**At every round start**, the coding agent has access to **both repositories**, reads their applicable `AGENTS.md` guidance, reads the **unchanged** frozen acceptance document, checks its recorded SHA-256, and compares the two implementation-branch heads to the previous round's evidence. A round is a paired **Al-Bayan + BuTeX** work session, not a separate independent sprint in each repository. If a repo needs no edits, record `N/A — verified` with why. Work only on the two long-lived **implementation** PR/MR branches opened **after the planning PR/MR have been approved and merged**; append small phase-labeled commits to those same open implementation requests rather than merging or replacing them between rounds.

**At every round end**, update each plan's *implementation-branch* round ledger (or linked PR/MR comment) with the same shared round ID and: both repository commit SHAs; environment and candidate worker/package/backend identities where used; changed-file summary; targeted commands and Developer MCP trace/report IDs; `passed / failed / partial / blocked / not_run` observations; whether each failure is an **expected intermediate contract break**; remaining risks; and the next safe starting point. Check both shared round boxes **only when the shared phase-specific exit gate is evidenced**. A known intermediate mismatch must be visible in the ledger, **not** hidden by compatibility aliases, skipped tests, unreviewed API changes or a false green status. Agent handoff text should explicitly state that the **full frozen acceptance matrix has not yet been executed** until Round 7.

**Phase-specific testing policy:** Round 0 writes/reviews/freezes only the acceptance oracle and naming/plan contract; Round 1 builds the Developer MCP harness and **captures a reproducible pre-rename baseline**. Rounds 2–6 use focused existing and newly added tests, CI and small diagnostics for fast debugging; they may intentionally leave the overall application/CI broken while APIs are being renamed. They **must not** amend the frozen specification or prematurely call the migration complete. After *all* code changes in Round 6, **Round 7** runs every mandatory acceptance ID and every prescribed repeated stress loop against attested, coordinated candidate builds. Store `migration-acceptance-report.json` plus a human-readable report **separately** from v1; any required failure/partial/blocked test keeps Round 7 unchecked.

**Add to Round-1 test-harness implementation:** a non-mutable CI guard that checks the recorded frozen-spec SHA-256 locally and, when both checked-out repositories are available, compares the two copies. A changed/missing spec or missing freeze hash must **fail/stop** migration verification rather than recalculating and silently accepting a new baseline. Keep this guard separate from the document regression suites so that focused interim test failures cannot disable specification integrity.

**Environment rule from** [Al-Bayan's Railway infrastructure inventory](https://github.com/Pontmousse/albayan/blob/develop/docs/development/railway-infrastructure.md): the persistent `development` frontend/backend/product MCP follow **`develop`**; production follows **`main`**. Unmerged implementation PR heads are **not automatically live** in that persistent environment, and the private BuTeX worker's deployed revision must be established independently. For headless/local candidate comparisons prefer a reproducible isolated worker and backend; use explicit approval and verified development-only targets for any staged live diagnostics. Temporary **development-only** breakage is allowed; **no** production deployment, production data test, backward-compatibility shim, early merge or npm publication is implied.

### Shared round-level completion ledger — mirror statuses/evidence in both plans

- [ ] **Round 0 shared gate:** v1 acceptance specification reviewed/frozen; **identical SHA-256** recorded for the two copies; no testing claimed passed.
- [ ] **Round 1 shared gate:** extra Developer MCP tools and safe backend/worker diagnostic adapters tested, fixture corpus and pre-migration behavioral baseline captured.
- [ ] **Round 2 shared gate:** complete source and stored-wire inventories cross-reviewed; shared math extracted; no unknown deletion dependencies.
- [ ] **Round 3 shared gate:** legacy first-generation GUI/model removed; shared behavior preserved; tracked interim failures acceptable.
- [ ] **Round 4 shared gate:** renamed headless worker/bin/routes + Al-Bayan backend client agree in isolated contract probes.
- [ ] **Round 5 shared gate:** renamed GUI/preview and Al-Bayan frontend consume the same candidate tarball and integrate in isolated tests.
- [ ] **Round 6 shared gate:** canonical backend/normal MCP names complete; both candidate pipelines and deterministic integration tests green.
- [ ] **Round 7 shared gate:** **all frozen mandatory acceptance and stress tests passed**, evidence report and both ledgers complete; human approval before release/merge/deploy.

## 7. Al-Bayan round-specific tasks (do not replace shared gates)

### Round 0 — contract authoring and freeze, Al-Bayan
- [ ] Review `docs/proposals/document-migration-frozen-acceptance-v1.md` against actual Al-Bayan and BuTeX service contract; verify mirror hash and owner approval.
- [ ] Confirm each acceptance ID is observable via Developer MCP, existing test/CI, normal MCP, Playwright or authorized compiler (never falsify an unsupported observation).
- [ ] Record initial Al-Bayan/BuTeX source SHAs and confirm `development`/production Railway branch separation.
- [ ] **Exit:** both repositories check the **same** Round 0 gate only on freeze approval.

### Round 1 — implement Developer MCP infrastructure, Al-Bayan primary owner
- [ ] Implement **narrow** `dev_document_contract_snapshot`, `dev_document_inspect`, `dev_document_compare`; bounded trace-linked stable schema, explicit `passed/failed/partial/blocked` and human actions; compare Git/build *snapshots*, not Burhan tiers.
- [ ] Implement or extend an authenticated, feature-gated stateless **development backend** diagnostic boundary delegating to the real BuTeX worker. No second parser; no arbitrary POST or production access.
- [ ] Register and test `document-contract-smoke`, `document-normalization`, `document-commands`, `document-references`, `document-math-roundtrip`, `document-export`, `document-error-contracts`, `document-final-stress` (stress is **not** executed yet). Preserve original equation coverage.
- [ ] Add offline/CI tests for auth/redaction, unavailable stages, provenance, trace propagation, regression report schema, comparison and deterministic fixtures; capture the **before-rename** baseline on a verified old dev/isolated worker.
- [ ] **Exit:** jointly verify the Round 1 shared harness/baseline gate with BuTeX contributions.

### Round 2 — audit and protect data/consumers
- [ ] Regenerate full frontend headless/React import map, backend `butex_worker_client`, FastAPI schemas/routes, normal MCP schemas/tool names, deployment variables, source-based consumer graph.
- [ ] Confirm `DocumentObject` JSON fields, frozen immutable revisions, command `op` wire discriminators and auth/revision semantics are to be **preserved**, and classify any serialized conflict before changes.
- [ ] Coordinate tests of four BuTeX extracted shared math utilities through worker math diagnostics and existing Al-Bayan equation path.
- [ ] **Exit:** no unknown Al-Bayan consumers of deleted/renamed symbols.

### Round 3 — legacy removal checkpoint
- [ ] Inspect impact of BuTeX first-generation code removal on Al-Bayan; update affected planned CI/source references as needed.
- [ ] Keep current Al-Bayan `Document2` consumers temporarily if the current maintained BuTeX implementation still uses those names; no shims needed and interim integration may be broken.
- [ ] **Exit:** shared removal gate recorded with BuTeX commit; no discarded preserved math/identity behavior.

### Round 4 — worker/client cutover
- [ ] Migrate `backend/app/services/butex_worker_client.py` operations to `/v1/document/*` and canonical schemas/route constants; keep HTTP `/v1/` protocol version intact.
- [ ] Update backend route/error/timeout/auth tests; verify real candidate worker `normalize`, `outline`, `references`, `reference-index`, `diff`, `export`, `commands` and math diagnostics against expected schema.
- [ ] Bind test outcomes to exact deployed/candidate worker revision; acknowledge transitory breakage before Round 6.
- [ ] **Exit:** identical request/response semantics with new active worker route names and zero permanent route aliases.

### Round 5 — frontend consumer cutover
- [ ] Update `frontend/package.json` / lock in **one commit** to a reproducible local candidate tarball, workspace test artifact or other precisely attested unreleased package workflow; **do not** publish npm merely to test.
- [ ] Migrate maintained GUI/headless imports in editor page, image asset picker, `butex-latex`, validation, autosave, article client, revision/frozen preview and `globals.css` widget selectors/injected styles.
- [ ] Test editor/preview separation, callbacks, RTL, numeral picker, MathJax/digit forms and CSS scope via component tests and focused browser probes when candidate is deployed.
- [ ] **Exit:** Al-Bayan frontend consumes same candidate BuTeX package as the integration report.

### Round 6 — finish public backend/MCP contract, CI
- [ ] Canonicalize Python typed Document schemas, FastAPI request/response names, `mcp_server/src/albayan_mcp/schemas/document2.py` and tools/docs, Developer MCP suite/stage names; preserve **actual serialized command `op` strings** unless separately approved.
- [ ] Confirm normal user MCP tool discovery exposes final document vocabulary, scopes, authenticated draft commands, revision semantics, and no old `Document2` active names.
- [ ] Run all Python backend/normal-MCP/Dev MCP tests, frontend `npm ci`, `npm test`, `npx tsc --noEmit`, `npm run build` and relevant CI workflows. Verify development worker/backend build identity, not just app package lock.
- [ ] **Exit:** deterministic candidate integration and both CI gates green; **no npm tag/publish required**.

### Round 7 — immutable-spec final stress and readiness
- [ ] Run every **mandatory ID** in the frozen spec via Developer MCP and independent public normal MCP/browser/compiler observation where required; repeat mandated stress counts without changing the spec.
- [ ] Verify authorized dev browser and APIs only, old revisions load unchanged, final worker route/CLI names, data/math/Auth/MathJax, full CI; record pass/fail/partial/blockers and build/trace evidence.
- [ ] Update **implemented architecture docs only after the code exists**; write a separate final result report (never modify the v1 acceptance spec).
- [ ] Prepare explicit human review for merge, major npm publication/tag/consumer lock and development deployment sequence; **no production actions**.
- [ ] **Exit:** the same Round 7 shared checkbox only after **all mandatory frozen checks pass** and owner approves next actions.

## 8. Cross-repo acceptance matrix

| Scenario | Where observed | Accept only if |
| --- | --- | --- |
| Package version + exports | candidate tarball, installed `node_modules`, manifest+lock; registry post-authorization | `document`, `react-document` and `react-document-preview` resolve maintained APIs, versioned generation-two subpaths do not; CLI is `butex-document` |
| Article editing and save | Browser/Next and FastAPI | Validated wrapper, image callback and `onDocumentJsonChange` work, revision conflict handling intact |
| Figures/captions/references | Current Document2 tests, preview, browser | Asset identifiers, captions, labels, bibliographic references survive roundtrip |
| Mathematics | Normal MCP, Burhan, Document2 worker, GUI | Canonical LaTeX is converted, stored MathObject reopens as editable (or reports real unsupported reason), SVG rendered |
| Arabic UX | Browser DOM + screenshot + CSS tests | Correct RTL, themes, numeral chooser, MathJax display, mobile toolbar |
| Frozen/history preview | Dedicated dynamic preview + revision storage | Same selected immutable revision, no editor chrome, correct styling/image assets |
| Security/identity | FastAPI/MCP tests | Auth and scoped draft changes preserved; no redirect to production |
| Development compiled output | Authorized development compiler | Same structured equations/refs/assets rendered consistently; required evidence recorded as blocked when unavailable |

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

**Recovery:** Keep the two accumulating implementation branches unmerged until final gates; revert individual commits or abandon a candidate PR/MR if blocked. Explicitly authorized development-only deployments may be temporarily broken; never modify production. If a new npm artifact has been published, do not rewrite that published tarball; pin Al-Bayan to its prior working version/lock and repair in new commits. Roll back development frontend/worker independently only after verifying current API compatibility; never mutate historical article revisions, authentication or production data to compensate for a GUI rename.

## 10. Definition of done

- [ ] BuTeX's [complete source-preservation, cleanup and GUI rename plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md) completed and final package tested/released with approval.
- [ ] Every active Al-Bayan editor, asset, style, frozen preview, test and documentation reference uses the final public GUI names; standalone equation/MathJax behavior survives.
- [ ] Candidate `frontend/package.json` and `frontend/package-lock.json` agree with an attested unreleased BuTeX artifact for final acceptance; **after separate approval**, update them together to the verified published major release and confirm registry integrity.
- [ ] Active headless `@drghaliasri/butex/document`, `DocumentJson`, `butex-document`, `/v1/document/*`, backend typed **Document** commands and normal MCP tool/schema names are canonical and unsuffixed; immutable draft/revision **JSON contents**, authorization/security and mathematical semantics remain unchanged.
- [ ] Frontend, backend, MCP, BuTeX CI and **development browser/MCP end-to-end evidence** pass every mandatory frozen-v1 test, including the final stress procedure.
- [ ] Every synchronized round evidenced in the same two accumulating implementation requests, with both shared gates and final approval; every future merge, publish and deployment separately authorized.

### Evidence provenance and limitations

Verified `develop` sources include Al-Bayan `frontend/package.json`, `frontend/package-lock.json`, editor page, `butex-mathjax.ts`, `butex-image-assets.ts`, frozen preview, `globals.css`, `article-editor-chrome.test.ts`, `history-ui-contract.test.ts`, `backend/app/services/butex_worker_client.py`, `article_draft_service.py`, `docs/architecture/mcp.md`, `.github/workflows/equation-integration-ci.yml`; cross-referenced BuTeX `src/document2/mathBridge.ts`, `src/document2/types.ts`, `src/react-document2/index.ts`, `tsup.config.ts` and the package manifest. Some repository-wide search hits identify further consumers; Round 2 requires a full re-run of a real checkout symbol/import graph after the Round 1 baseline snapshot. **No tests, runtime release, MCP diagnostic, Playwright browser session or CI pipeline were executed for this documentation-only task.** No claims of a passing integration test are made.
