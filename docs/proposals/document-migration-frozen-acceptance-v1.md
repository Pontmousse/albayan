# Frozen cross-repository Document migration acceptance contract (v1)

> **PHASE 0 SPECIFICATION — PROPOSED, NOT YET FROZEN OR EXECUTED.** Authored for the linked Al-Bayan GitHub PR #236 and BuTeX GitLab MR !66. This file must be **identical in both repositories**. On approval/merge of the planning requests, Phase 0 records its content SHA-256, and the exact version becomes the **read-only acceptance oracle** through implementation rounds 1–6. Do not edit or relax it to make a failing migration pass. Only after the implementation is complete does the agent run the **entire** acceptance/stress protocol in Round 7. If a defect in the frozen specification is discovered, create a separately reviewed, explicitly versioned addendum; retain this v1 unchanged and report the deviation. Do not silently alter test requirements.

**Canonical relative path (both repos):** `docs/proposals/document-migration-frozen-acceptance-v1.md`. **Scope:** one generation-neutral active document architecture across BuTeX (GitLab `drghaliasri/butex`) and Al-Bayan (GitHub `Pontmousse/albayan`). **Status language:** all checks below are **expected future outcomes**, not claims of observed passes.

## A. Goals, authority, boundaries

1. The final active code/API uses unsuffixed `Document` naming everywhere in the maintained editor, preview, headless model/types, imports, CSS, CLI, HTTP routes, worker, FastAPI, and normal user MCP. `v1` remains the HTTP protocol version; numeric mathematical notation and unrelated legitimate uses of “2” are not rename targets.
2. Delete the obsolete first-generation BuTeX document GUI/model only after extracting genuinely shared math utilities; preserve maintained standalone equation editor, Burhan integration, MathJax and XeLaTeX/export.
3. **Do not change persisted document JSON shape/meaning** as a consequence of naming: `node_type: "DocumentObject"`, blocks, token and field IDs, `MathObject`/`RawMathObject`, metadata, `asset_id`, labels, revisions and references keep their stored semantics. No mass rewrite of immutable revisions. If a genuine persisted discriminator conflicts with the rename, stop and request a separately approved schema migration; do not weaken these tests.
4. **No compatibility promise in intermediate migration rounds.** The dedicated unmerged implementation branches may fail build/tests/API interoperability. No temporary aliases/shims or dual old/new endpoints are required; the **final** product must expose only the canonical generation-neutral contract. Intermediate green tests are diagnostic, not round-completion requirements.
5. The Developer MCP is the **headless diagnostic/orchestration plane**. It uses actual, allowlisted development Al-Bayan/BuTeX/Burhan services and the real document worker; it must not duplicate the document parser/serializer or use unrestricted POST. Browser reality requires the **separate Playwright MCP**; real authoring schema/auth must be verified through the **separate normal Al-Bayan MCP**. The *same AI agent* can use all three as independent evidence sources during the final round.
6. No production browser/API/MCP/worker/DB, no production article mutations, no production deployment or secrets. The persistent Railway `development` environment uses Al-Bayan `develop`; `main` feeds production. Verify the independently deployed BuTeX worker provenance, not merely the frontend npm version. Docs: Al-Bayan `docs/development/railway-infrastructure.md`, `developer-mcp.md`, `playwright-mcp.md`, `mcp-operations.md`, and `dev_mcp_server/README.md`.
7. Use **synthetic, disposable, explicitly authorized development-only data**; do not stress or mutate user drafts or actual production-like data. Headless diagnostics should default to nonpersistent operations. A final live normal-MCP/browser scenario may create a dedicated test draft via authorized product APIs, with cleanup governed by normal permissions.

## B. Required test harness and frozen fixture definitions

**Required proposed Developer MCP capabilities (implement in Round 1):**
- `dev_document_contract_snapshot`: obtain configured development build/commit/version identities and read-only contract metadata from a trusted service or CI-produced attestation; classify unknown build identity as **partial/blocked**, not as compatible. Capture package export map, CLI entry, worker route operation map, FastAPI client expectations, normal-MCP schema/tool discovery summary, and the expected canonical name map. Never return credentials.
- `dev_document_inspect`: exercise explicitly allowlisted **stateless, authenticated** document worker operations on supplied bounded fixtures through an approved backend diagnostic endpoint/adapter: normalize, outline, commands, references, reference-index, diff, export, math-object import and projection. Include trace ID, stage/status, timing, structural invariants and bounded sanitized evidence. No unrestricted generic HTTP POST or DB mutation.
- `dev_document_compare`: compare two **previously collected** immutable baseline/candidate reports, or two configured allowlisted builds, for exact and semantic invariants. Must **not** pretend that `dev_investigation_report(compare_model_tier=...)` compares Git revisions; that existing argument compares Burhan model tiers only.
- Register named suites through existing `dev_regression_suites`, `dev_run_regression_suite`, `dev_investigation_report`: `document-contract-smoke`, `document-normalization`, `document-commands`, `document-references`, `document-math-roundtrip`, `document-export`, `document-error-contracts`, and `document-final-stress`. Preserve `equations-smoke`, `equations-adjacency`, `equations-common-scientific`, existing tier probes and trace lookup. Rename the existing `document2-roundtrip` suite and `document2_command` stage to unsuffixed names at the final cutover, while retaining their meaningful fixture coverage.

**Frozen synthetic fixture seeds** (materialize deterministically with stable IDs and record normalized bytes/hash; adapt only syntactically to the actual documented command schema, without changing the semantic purpose):
- `D0-empty`: `{"node_type":"DocumentObject","blocks":[]}`; normalization may supply documented default metadata/IDs; capture expected post-normalization canonical representation at baseline.
- `D1-arabic`: metadata title `اختبار المستند`, author `باحث`, abstract `ملخص تجريبي`, Hijri date; section, paragraph containing Arabic digits `١٢٣`, Latin `x`, punctuation, diacritics and Unicode; repeat normalization, import/export.
- `D2-structure`: section/subsection, ordered/unordered list with nested child blocks, table with multiple rows/columns, bibliography, optional raw block; stable block and inline field IDs.
- `D3-figures`: image with `asset_id: "dev-fixture-image-001"` (mock asset only), caption with label, table caption/label, reference to each; asset ID must survive edits and export list deduplicate.
- `D4-references`: two bibliography records, citation keys, `ref` and `eqref`, Arabic and comma separators, resolved and intentionally unresolved keys; update/rename/move/remove exercises.
- `D5-math`: inline and display supported canonical English LaTeX fixtures: `x^2 + y^2 = z^2`, `\\frac{a}{b}`, `\\sqrt{x}`, `\\sum_{i=1}^{n} i`, `\\int_0^1 x\\,dx`, `\\frac{\\partial f}{\\partial x}`, `\\theta`, `\\begin{cases}x&x>0\\\\0&x\\leq 0\\end{cases}`; include editable `MathObject`, supported labels, and a separately flagged `RawMathObject` case that must not be falsely reported editable.
- `D6-history`: at least two immutable synthetic draft revision snapshots, one with missing optional block IDs/legacy defaults, one with explicit IDs, figure/inline math; never silently rewrite either original snapshot.
- `D7-invalid`: deliberately invalid `node_type`, malformed blocks, missing/duplicate keys or invalid anchors, nonexistent block/token, invalid table index, malformed math object, oversized request and unauthorized worker request.
- `D8-diff`: two semantically distinct synthetic documents with additions, removals and unchanged context; verify deterministic `version: 1`, `changed`, `truncated` and bounded chunks.

The above examples specify **semantic fixtures**, not fabricated already-valid complete payloads. Round 1 harness must construct full valid payloads using the existing authoritative BuTeX types and command schemas (see `src/document2/types.ts` and `src/document2/jsonCommandTypes.ts` in the pre-migration baseline). Persist an immutable **baseline report artifact** separately from this frozen document, with source commits, fixture JSON, normalized outputs, captured differences and the environment/build manifest. The baseline can be gathered against the old `document2` implementation before cutover; comparisons must explicitly map **old interface names** to **new names** while preserving behavior.

## C. Fixed test matrix and expected validations

The final AI agent must report **every test ID** with `passed | failed | partial | blocked | not_run`, input/fixture ID, observed versus expected, trace/build evidence, and source of observation. `partial`, `blocked` or `not_run` cannot be called a complete pass. Do not silently skip tests; only explicitly marked optional tests may be `not_applicable`.

| Test ID | Required action / fixture | Required acceptance oracle |
| --- | --- | --- |
| ENV-01 | Inspect actual Railway development service and API/worker origins | All tested service targets explicitly development; **zero production origins, redirects, writes or credentials** |
| ENV-02 | Snapshot Al-Bayan backend/frontend/normal MCP, BuTeX worker and relevant package build IDs | Actual compatible candidate source revisions/versions attested; missing provenance is **partial** |
| ENV-03 | `dev_capabilities`, `dev_health`, named suite discovery | Available and reachable required dev tools/services; meaningful explicit blocker otherwise |
| ENV-04 | Traces through Al-Bayan → BuTeX and Al-Bayan → Burhan | Correlated `X-Trace-Id`; missing downstream source explicitly identified, not invented |
| ENV-05 | Run diagnostics without permanent article state changes | No DB/draft mutations caused by Developer MCP inspection |
| NAM-01 | Build exact TypeScript package export/import probes | Current GUI at `@drghaliasri/butex/react-document`, preview at `.../react-document-preview`, headless at `.../document`; declarations resolve |
| NAM-02 | Check canonical types/functions and React declarations | Unsuffixed `ButexDocumentEditor`, `DocumentJson`, `DocumentNode`, import/export/validation/commands and CSS injector API; named expected exports compile |
| NAM-03 | Inspect `bin`, executable help, worker health/service identity | `butex-document` exists/starts and worker service identity is unsuffixed |
| NAM-04 | Route discovery + authenticated requests through worker | `/v1/document/{normalize,outline,references,reference-index,export,diff,commands,diagnostics/math-object,math-object/english}` dispatch correctly |
| NAM-05 | Test removed generation-two routes, exports, bin and old GUI | `/v1/document2/*` returns 404 (with valid worker auth), removed `document2` package exports/CLI and old GUI no longer active; **no permanent aliases** |
| NAM-06 | Audit runtime source, generated exports/CLI help, FastAPI and normal MCP schema | No active generation-two document naming; archived historical migration evidence may still name old API |
| NAM-07 | Serialize `D0-D6` across old/canonical implementations | Wire `node_type: "DocumentObject"` and material JSON semantic fields unchanged; `/v1/` remains protocol version |
| SHR-01 | Dependency graph across BuTeX shared math, CLI and standalone editor | Four shared modules extracted before deletion; no current preserved consumer imports deleted legacy files |
| SHR-02 | Run existing standalone math, MathJax and Arabic font/digit normalization tests | Same supported parse/serialize/editor behavior and no deleted shared tests |
| DOC-01 | Import/export/normalize `D0` and `D1` | Valid `DocumentObject`; no unexpected structural drop or failure |
| DOC-02 | Normalize each `D0-D6` twice | **Idempotence** `N(N(D))=N(D)` for canonical normalized output |
| DOC-03 | Import and export `D1-D4` without edit | Same semantic content, formats, metadata, Unicode and citation fields as baseline (ignore only documented benign canonicalization) |
| DOC-04 | Compare immutable snapshots `D6` before/after conversion | Original stored snapshots unchanged; old revision loads with preserved meaning |
| DOC-05 | Check IDs through normalize, update and move | Unaffected block/item/field/token IDs remain stable; generated IDs unique and deterministic where contract requires |
| DOC-06 | `D1` Unicode and Arabic authoring values | Arabic script, diacritics, digit forms, punctuation, RTL intentions retained without lossy conversion |
| CMD-01 | Text `insert_text_block`, `replace_text_block`, `remove_block` | Correct order/content and scoped changes only; preserved unrelated IDs |
| CMD-02 | `move_block` with before/after/end anchors | Exact deterministic ordering; invalid anchor returns typed failure |
| CMD-03 | `update_document_meta` and Hijri date | Title/authors/abstract/date patches correct, no unrelated loss |
| CMD-04 | `insert_figure`, `update_figure`, `update_float_meta` | Asset identity, caption/label/center metadata, text semantics survive |
| CMD-05 | `insert_list` and list item insert/replace/move/remove | Stable ordering, content and nested structure |
| CMD-06 | `insert_table`, cell replacement, row insert/remove/move | Rectangular table invariants and expected targeted edits |
| CMD-07 | Table column insert/remove/move | Column specification, cell content and indices consistent |
| CMD-08 | `insert_bibliography`; reference insert/update/move/remove | One bibliography and ordered valid reference set; duplicate/unknown keys typed failures |
| CMD-09 | Inline insert/replace/remove `text`, `math`, `cite`, `ref` | Token positions/IDs and payload meaning stable; unsupported math never silently coerced |
| CMD-10 | Command chain run via stateless worker stdin and HTTP | Equivalent normalized document and structured error codes across transports |
| CMD-11 | Apply one command with invalid block/token/anchor/index | No partial mutation; documented `DocumentCommandError`-equivalent typed code and HTTP 422 where applicable |
| REF-01 | `D4` references and index | Numbering, keys, citations/cross-references, resolved/unresolved buckets correct |
| REF-02 | Rename reference/label, update cite/ref tokens | Relevant references updated; unrelated citations unchanged; no duplicate collisions |
| REF-03 | Image/table/equation label references | Labels and numbering survive normalization, commands, preview and export |
| REF-04 | `D3` asset references/duplicate images | `asset_id` preserved; export `asset_ids` unique and exact; missing image content not invented |
| DIF-01 | `D8` diff | `version: 1`, stable `changed` and valid bounded `added/removed/context` chunks |
| DIF-02 | Diff identical normalized documents | `changed=false`, empty change chunks, no false positives |
| EXP-01 | Export `D1-D5` to LaTeX using actual worker | Nonempty deterministic well-formed output, structural commands intact, no dropped supported content |
| EXP-02 | Export citations/labels, Arabic title/Hijri metadata and figure/table captions | Cross-references and Arabic text survive; no broken escaping or orphaned labels |
| EXP-03 | Re-export after normalized roundtrip | Semantically equivalent XeLaTeX, same asset IDs; formatting-only differences must be explained |
| MTH-01 | Existing deterministic equation suites | All supported heuristic fixtures and MathObject projection succeed with no semantic regression |
| MTH-02 | Supported `D5` inline/display equations | Canonical LaTeX → real Burhan → Al-Bayan projection → worker command → BuTeX headless editable import succeeds |
| MTH-03 | Reverse math conversion/reparse | Normalized **semantic AST equivalence**, not raw LaTeX string equality; changed operators/case are failures |
| MTH-04 | Unsupported/raw/malformed math cases | Explicit noneditable/typed failure; never report unsupported expression as roundtrip-safe |
| MTH-05 | Scientific operator/adjacency/regression fixtures | No regressions for derivatives, `dx/df/kx`, matrices, sums, cases, fonts and delimiters |
| MTH-06 | Math diagnostics and projection worker operations | Unsuffixed diagnostic path and real headless adapters return stage-resolved evidence |
| ERR-01 | `D7` invalid JSON/document/command/table/maths | Stable structured error family, safe bounded issues; no 500 for documented invalid inputs |
| ERR-02 | Worker request without/with wrong token | 401 and no document processing; no credential exposure |
| ERR-03 | Oversized request and unsupported method/path | 413 / 404 per contract; bounded sanitized outputs |
| ERR-04 | Normal MCP unauthorized / stale revision / duplicate command replay | Scope checks and immutable revision conflict/idempotency policy preserved; no unauthorized write |
| INT-01 | FastAPI → configured worker `/v1/document/*` for all used operations | Real backend client and worker versions agree; no 404 or schema mismatch |
| INT-02 | Normal MCP discovers final typed Document authoring schema/tools | Final canonical names visible to a real user-facing client; not inferred from Dev MCP |
| INT-03 | Authorized normal MCP typed command on disposable dev draft | One correct immutable revision increment and the expected command result, then read/reopen same content |
| INT-04 | Dev-only revision history, concurrency, autosave and restore | Stable ID/revision behavior, conflicts detected; old saved snapshots not rewritten |
| UI-01 | Separate Playwright MCP browser on `https://dev.albayan-journal.org` | Authenticated editor loads, correct dev API calls, no production redirects, console errors or crashed UI |
| UI-02 | Edit Arabic RTL text, headings/list/table and save/reopen | Persisted content, caret/editability, spacing and Arabic typography survive |
| UI-03 | Insert/reopen an equation from actual dev authoring flow | Arabic mathematical representation and editable MathJax/BuTeX session correct; SVG/DOM observed |
| UI-04 | Insert existing authorized dev image, caption, reference and navigate preview | Asset/label/rendering correct, no broken picker or CSS |
| UI-05 | Dedicated frozen revision preview, history and autosave conflict UI | Light preview works; no full editor unnecessarily required; expected messages shown |
| UI-06 | CSS scope, numeral picker restrictions, preview style injection, responsive layout | Canonical widget selectors match DOM; no stylesheet duplication or global RTL regressions |
| CMP-01 | Authorized development XeLaTeX compilation of `D1-D5` representative supported fixture | PDF succeeds where compiler is configured; Arabic typography, equations, figures and references consistent; failure is a blocker unless explicitly approved as environment-unavailable |
| PKG-01 | BuTeX final `npm ci`, build, types, lint, tests, pack and CLI smoke | Green final pipeline, expected CJS/ESM/d.ts and bin in tarball; no deleted legacy imports |
| PKG-02 | Al-Bayan frontend build/types/tests and backend/user MCP/Dev MCP pytest | Green final pipelines and actual dependency build compatibility |
| PKG-03 | Consume final candidate BuTeX tarball in Al-Bayan **without npm publication** | Same package artifact/exports expected by the frontend; lock and integrity plan reproducible |
| PKG-04 | Deliberate breaking API audit | No invisible runtime compatibility shims for former generation-two exports, routes or commands |
| REL-01 | Final evidence and explicit approval review | No publish, tag, merge or production rollout implied by a test pass; release requires separate authorization |

**Final audit must include:** all still-relevant named existing BuTeX tests (document2*, shared math/MathJax), Al-Bayan backend/editor/history/MCP tests, existing deterministic equation suites, and any tests added in migration. Renaming an old test file must not drop its behavioral assertions. An inventory of affected original tests, disposition, and equivalent migrated tests is required.

## D. Stress procedure and objective stopping rules (Round 7 ONLY)

1. **Preflight:** verify identical frozen spec bytes in both repos; record their SHA-256 hashes, both commit SHAs, actual development deployment build IDs and package tarball SHA/integrity. Abort or report `blocked` if not enough trustworthy provenance to identify the candidate.
2. **Run complete matrix once** against the final candidate and all supported fixture variants. Reuse existing Dev MCP investigation reports and `X-Trace-Id` where appropriate. Execute normal-MCP, browser and compiler cases independently rather than disguising them as headless Dev MCP evidence.
3. **Repeat deterministic stress:** at least **100 consecutive in-memory normalize/import/export cycles** per `D0-D6` fixture with equal normalized semantics; at least **25 iterations** each for representative text, list, table, figure, citation and math command chains via actual worker/CLI, with zero divergence, unexpected 500s, ID collisions or state mutation. At least **20** bounded, serialized authenticated requests to each required worker operation (not a load/DoS test). Use a disposable isolated backend/test worker where appropriate; avoid stressing a shared production-like development DB.
4. **Error and authorization stress:** repeat malformed-input and invalid-token probes with strict rate/size limits; expect only prescribed validation/status behavior and no confidential data leakage. Do not brute-force credentials.
5. **Concurrency and client stress:** under approved dev test account, test two stale-revision/conflicting updates and idempotent command replay; at least **three** full normal-MCP → backend → worker → saved revision → real browser reopen cycles on disposable drafts, each with distinct Arabic/math/reference content.
6. **Render consistency:** inspect at least one desktop and one mobile viewport, RTL/MathJax, preview, image, autosave/history and an actual development compile of supported fixture material.
7. **Decision:** **PASS** only if every mandatory test has observed `passed`, no persisted semantic regression, no old active API, no production origin, final CI is green, and all repeated deterministic stress iterations succeed. **FAIL** on an observed contradiction; **PARTIAL/BLOCKED** if required evidence cannot be collected. Do not count a missing observation or a known failure annotation as success.
8. **Evidence artifact (not an edit to this spec):** create `migration-acceptance-report.json` and a concise Markdown report in CI artifacts or a dedicated report file/PR comment, containing each test ID, fixture, expected/observed evidence, baseline/candidate versions, trace IDs, first failing boundary with uncertainty, CI job URLs, exceptions, timing, security checks and final status. The agent can fix implementation and rerun tests, but **cannot change this v1 acceptance contract**.

**Provider-backed/nondeterministic Burhan tiers:** default merge gates use deterministic `heuristic` and semantic AST comparisons. Cheap/medium comparison remains opt-in evidence, budget-limited, and is **not** a blanket mandatory pass threshold; actual user-path canonical interoperability must still be verified. Do not manufacture thresholds from unknown external model behavior.

## E. Ownership and completion rule

- **Al-Bayan** owns Developer MCP tool/harness implementation and registration, FastAPI diagnostic boundary, backend/normal-MCP consumers, frontend and final development/browser/orchestration evidence.
- **BuTeX** owns shared math extraction, obsolete editor removal, canonical headless/GUI/CLI worker changes, source/worker fixtures and package verification.
- **Both** own identical spec bytes, deterministic baseline/candidate fixture compatibility, test provenance, and a synchronized **Round 0–7** completion ledger. A round is complete only when **both repositories** record the shared gate as passed (or an explicit `N/A — verified no code changes` for a local subtask), backed by evidence. A passing single-repository test is not a shared round pass.
- The preferred implementation is **one long-lived unmerged PR in Al-Bayan plus one long-lived unmerged MR in BuTeX**, each with reviewable per-round commits/checkpoints. This frozen test spec is committed with the **planning** PR/MR now and is not modified during implementation. Do not merge these implementation requests, publish npm, tag a release or deploy production without later explicit approval. Development deployment is a separate, explicit environment-scoped act and may be temporarily broken during migration.

**Spec freeze:** Phase 0 is complete after owner review, byte-identical mirroring and recorded hash; **no tests are asserted passed by this document**. The **full acceptance/stress run is deferred until Round 7** after all migration changes have been implemented.
