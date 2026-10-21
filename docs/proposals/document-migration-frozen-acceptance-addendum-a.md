# Frozen Document migration acceptance addendum A — extended regression coverage

> **PHASE 0 OWNER-APPROVED ADDITIVE SPECIFICATION; NEVER EDIT THIS FILE IN PLACE.** This addendum augments, never replaces or weakens, [frozen acceptance v1](document-migration-frozen-acceptance-v1.md), whose verified SHA-256 is `6457a3d1abe43ba4cde16bd9b287d097978671db5ba3657c28099b1c6e26ca8e`. Identical copies of this addendum belong in the **Al-Bayan GitHub PR #236** and **BuTeX GitLab MR !66**. Phase 0 was explicitly authorized by the owner on 2026-10-21; the addendum content hash must be recorded in **both** plans after file creation and checked at every later round. All cases are proposed final *acceptance requirements*, not assertions that runtime tests have run or passed.

## 1. Why the addendum exists

The v1 specification already defines **66 unique mandatory acceptance IDs**, synthetic fixtures D0–D8, complete end-to-end checks, and Round-7 repetition/stress. A source-level re-audit of BuTeX maintained `src/document2/`, `src/react-document2/`, `test/document2*.test.*` and Al-Bayan authoring/backend/MCP/frontend tests found additional behaviors that could regress under full-stack renaming. This addendum makes those independently observable instead of relying on broad labels such as “editor works.” It adds **79 mandatory acceptance IDs** across 7 families; the complete frozen contract is **145 mandatory IDs**, plus the original v1 stress protocol. The final agent must run and account for **every** v1 and addendum ID, as well as *every retained relevant pre-migration test*.

**Scope limits:** Preserve all currently implemented document-authoring, equation, review/history, export and integration behavior touched by the migration; do not invent unimplemented book/thesis features or change document semantics. A genuinely unrelated feature is out of scope unless the touched code breaks it. No test can prove the absence of every imaginable bug, so combine exhaustive source-backed feature inventory, property/invariant testing, expected-failure tests, and real cross-boundary runs.

**Non-negotiable invariants:** Full canonical unsuffixed Document API; `/v1/` HTTP protocol prefix stays; `DocumentObject`, `MathObject`, `RawMathObject`, stored revision/ID/reference/asset semantics remain compatible; obsolete generation API cannot be retained as a shim. Intermediate unmerged branches may be broken with recorded targeted failures; only the final coordinated candidate must satisfy the full contract.

## 2. Evidence sources, procedure and scope coverage

At Round 1, create a **source-to-acceptance coverage manifest** separate from these frozen documents. For each real public entrypoint, UI command, typed union variant, endpoint, test file and retained behavior, record (a) pre-migration source and test, (b) final source and test or explicit validated deletion, (c) corresponding v1/addendum ID, (d) evidence mode and (e) run result. Automatically fail the *final* completeness gate on unmapped maintained operations, silently deleted assertions, skipped suites, test-only stubs, intentionally disabled errors, or a candidate whose build provenance is unknown. Store fixture inputs/outputs, observed baselines and reports separately, never in these frozen documents.

**Observation ownership:** Developer MCP orchestrates real stateless authenticated Al-Bayan/BuTeX/Burhan diagnostic paths and produces traces; direct local/CI unit and package tests prove source/CLI contracts; the **normal product MCP** proves actual authoring schema, auth and persistence; the **separate Playwright MCP** proves browser/DOM/keyboard/mobile/MathJax behavior; development compiler proves PDF. A Developer MCP report must mark those external observations absent until captured independently. No arbitrary shell/POST/database access is added to the Developer MCP, and no production operations or secrets are authorized.

**Outcomes:** Every ID is `passed`, `failed`, `partial`, `blocked` or `not_run` with expected/observed evidence, both repo commit SHAs, candidate package/backend/worker identities and trace/CI/browser/compiler references. **All IDs in this addendum are mandatory**; optionality is not introduced implicitly. A previously known baseline defect must be reported and dispositioned; `known_failure` metadata never converts failure into success. CI assertions and snapshots must remain meaningful after rename, not mechanically changed to false-green.

## 3. Additional frozen mandatory acceptance matrix

### INV — Inventory, public surface and retention

| ID | Required probe | Expected validation |
| --- | --- | --- |
| INV-01 | Inventory every pre-migration BuTeX `test/document2*.test.*` assertion and all maintained standalone math/MathJax tests | Evidence maps each test/assertion to retained, replaced-equivalent, or genuinely obsolete-only coverage, with source path, rationale, and actual final run; no silent deletion, skipped test, or weakened assertion counts as pass |
| INV-02 | Inventory every touched Al-Bayan backend, frontend, normal MCP, Developer MCP, and CI test | All relevant existing tests still execute or have source-traceable replacements; no removed route or renamed module leaves uncovered live consumer behavior |
| INV-03 | Enumerate the authoritative typed normal-MCP document command union against the baseline | Every maintained command variant (29 variants in inspected pre-rename schema) remains discoverable under final canonical names with equivalent payload validation and behavior; explicit mapping per variant |
| INV-04 | Enumerate BuTeX package exports, React types, CLI bins, worker operations, CSS entrypoints, ESM/CJS and TypeScript declarations | Required maintained surfaces exist in built *candidate tarball*, obsolete generation names are absent, and every consumer import and CLI route is accounted for |
| INV-05 | Enumerate backend/normal-MCP routes, worker client methods, and deployment environment variables | All names and call sites in affected source/tests/docs/CI/config map to the intended final contract; identify historical-only names without deleting historical evidence |
| INV-06 | Capture all baseline-supported user actions from the editor's toolbars, panels, dialogs, shortcuts and imperative host interfaces | A machine-readable action-to-test inventory covers every action; unavailable/uncovered actions are explicitly failed/partial until tested |
| INV-07 | Preserve exact build and test provenance for each reported run | Both repo commit SHAs, package tarball digest, worker revision, backend/frontend/normal MCP revisions, suite version, fixture ID and trace IDs are recorded; no unverified live-candidate assumptions |

### HED — Headless documents, structure and serialization

| ID | Required probe | Expected validation |
| --- | --- | --- |
| HED-01 | Normalize legacy documents with missing IDs and nested list/table/inline fields | Canonical IDs generated correctly, nested ownership stable, repeated normalization idempotent; no duplicate IDs or identity theft |
| HED-02 | Import documents with duplicate/misaligned block/item/cell/token IDs | Conflicting IDs repaired deterministically where specified, without transferring an ID to a different semantic token or block |
| HED-03 | Apply document commands to frozen inputs | Inputs and unrelated nested metadata are deep-cloned/not mutated; output changes only the intended fields and validates atomically |
| HED-04 | Select contiguous blocks, extend selection with Shift, uncheck endpoints/middle, then move/delete as a range | Selection, anchors, range remapping, edge no-ops and ordered results match pre-migration behavior; source helper and browser integration checked independently |
| HED-05 | Split and toggle formatted text around inline math | Formatting changes text ranges without accidentally styling/editing MathObject tokens; heading and caption restrictions unchanged |
| HED-06 | Insert inline/display math at a specified text caret position and continue typing | Correct source order, stable token IDs, trailing text token when needed, retained prose and focus/caret placement |
| HED-07 | Round-trip structured math inside multiple figure/table captions | Caption field IDs and equation IDs stable; caption math does not migrate into body or table cells |
| HED-08 | Round-trip multiple table-cell mathematical objects and nested list table cells | Cell associations remain row-major, nested command targets correct and independent of caption math |
| HED-09 | Import/export legacy plain captions and structured captions | Legacy caption promoted on import where intended, semantic text preserved; no need to fabricate sidecars or lose labels |
| HED-10 | Import and update article metadata, including Hijri dates and basmala/chrome | Arabic and older Latin Hijri month identifiers accepted according to documented contract; missing fields and invalid patches handled; title/authors/abstract/date stable |
| HED-11 | Test paragraph centering, heading/paragraph/list/table and raw-content boundaries | Center environment and semantic preview correct; supported raw blocks preserved in document/export even where deliberately omitted from preview |
| HED-12 | Validate Arabic/Latin reference and label keys, Unicode NFC normalization and namespace collisions | Documented allowed characters pass, invalid and normalized duplicate keys fail; references and labels share enforced namespace |
| HED-13 | Rename a citation key inside multi-key citations in every inline field | Atomic propagation across paragraph, list, table, caption and nested fields, preserving unrelated keys and field separators |
| HED-14 | Verify Arabic/English citation label ordering and digit form | RTL displayed citation order/separators/digits and corresponding logical LaTeX `\cite` key order match baseline; LTR comma override remains supported |
| HED-15 | Check bibliography href normalization and references metadata | Schemeless supported links normalize as documented; unsafe/invalid reference keys do not cause silent edits |
| HED-16 | Compare diff reports across property reordering, legacy generated IDs and large unchanged context | Equivalent content reports unchanged; deterministic chunk kinds and size/truncation limits; no false positives from benign JSON key order |
| HED-17 | Strict/non-strict invalid math import and malformed documents | Strict mismatch fails explicitly; non-strict diagnostic preserves raw content; invalid draft remains recoverable across save/reopen; guarded export refuses invalid data |
| HED-18 | Check record provenance and metadata unknown-key handling | Known source provenance preserved/exposed only where present; unknown fields handled per established import contract; unrelated metadata and IDs never leak between document instances |
| HED-19 | Verify figure identity independently of image value and float metadata | Asset ID, caption, label, alignment and provenance remain independent through updates/clears; empty-figure validation unchanged |
| HED-20 | Verify exported text/preamble variants | Default full XeLaTeX, body-only option, two-column class, digit mapping, Arabic preamble/macros and structured table column specifications preserve baseline behavior |

### EDT — Desktop editor, accessibility and interactions

| ID | Required probe | Expected validation |
| --- | --- | --- |
| EDT-01 | Exercise equation drawer insert, edit, save, cancel, reopen and delete on actual GUI | Cancelled edits do not persist, newly inserted equation receives expected focus, existing IDs stable, English/Arabic side semantics unchanged |
| EDT-02 | Exercise equation drawer for caption equations | Same supported drawer pathway and stable caption token IDs; no destructive mutation of other caption or body math |
| EDT-03 | Exercise inline caret/arrow navigation between text and math chips in both prose directions | Visual direction, selection, focus and noneditable boundaries operate without mistaking equation direction for document direction |
| EDT-04 | Exercise selection move/delete, undo/redo and focus restoration using toolbar and keyboard | One user action has one intended undo unit, redo restores identical semantic document and no ghost selections remain |
| EDT-05 | Exercise clipboard, paste, Unicode/diacritics, and safe text-token editing | Arabic/Latin mixed content and mathematical tokens survive copy/paste and editing; no hidden raw LaTeX inadvertently becomes editable plain text |
| EDT-06 | Exercise document insertion toolbar and all supported menu callbacks | Every advertised insertion/format/reference/structure action is reachable and results in the intended typed command rather than an inert control |
| EDT-07 | Exercise host imperative image API and both picker fallbacks | Insert after focused block, update value, resolve host URL, request picker/list fallback, and clearing asset retain caption/label |
| EDT-08 | Exercise article metadata panel and invalid-figure validation UI | Arabic and English localized errors; invalid initial input reported invalid, not silently replaced with an empty document; validity callback emits initial and changes only on boolean transition |
| EDT-09 | Exercise both editor and preview panes, collapse/expand, debug JSON/TeX controls | State survives mode/panel toggles where designed; preview uses the same canonical content; debug outputs match actual headless result |
| EDT-10 | Exercise independent GUI language, prose RTL/LTR and equation-side settings | Changing one setting does not silently change the other; Arabic UI localization and mixed scientific text remain legible |
| EDT-11 | Exercise actual MathJax SVG islands and CSS resets | Equation chips/previews remain visible and aligned under host Tailwind resets; no disabled editing controls appear within read-only MathJax islands |
| EDT-12 | Verify CSS injection and host component styling | Idempotent injector, canonical selector names, scoped rules and no duplicate style tags, title/figure/list breaks, or leakage into unrelated app surfaces |
| EDT-13 | Verify saved frozen revision preview replacement | Preview updates when supplied a different revision, never shows stale previous content, avoids full editor machinery, supports asynchronous image resolver and localized malformed-data errors |
| EDT-14 | Verify runtime `onChange` and canonical JSON callbacks plus invalid-initial-state behavior | Callbacks remain distinct and type-correct; runtime math objects are not accepted after a destructive JSON de-prototyping operation; malformed data remains reported, not overwritten |
| EDT-15 | Check accessibility of major keyboard-operated editor workflows | Focusable controls have accessible names, predictable Tab/Shift-Tab/Escape operation, no focus traps outside intentional dialogs, RTL navigation remains functional |

### MOB — Responsive/mobile editor behavior

| ID | Required probe | Expected validation |
| --- | --- | --- |
| MOB-01 | Switch mobile Edit/Preview workflows and desktop panels repeatedly | Correct mounted panel/state preservation and consistent content; mobile mode force-propagates to equation drawer only where intended |
| MOB-02 | Open all mobile toolbar structure/content/equation/reference/table submenus | Each action is discoverable and routes to same canonical command/validation as desktop |
| MOB-03 | Exercise compact block navigation, collapse, undo/redo and editing commands | Operation targets correct focused block and exposes expected reversible change |
| MOB-04 | Open mobile More sheet and manager modal dialogs | Focus trapped while sheet is open, Escape closes, focus returns to trigger, nested managers remain keyboard accessible |
| MOB-05 | Switch between desktop and mobile viewport sizes with RTL text/math/tables/images | No lost buttons, horizontally clipped critical controls, incorrect SVG mirroring, or stale editor selection after responsive transition |
| MOB-06 | Use read-only preview on a mobile viewport | No editing toolbars, hotkeys or hidden mutable editor state instantiated; preview semantics match desktop |

### WRK — Worker, transport, runtime and artifacts

| ID | Required probe | Expected validation |
| --- | --- | --- |
| WRK-01 | Compare stateless worker stdin and HTTP for all public document operations | Normalization, commands, outline, references/index, diff, export and math diagnostics yield semantically equivalent success/error results |
| WRK-02 | Test exact HTTP path, method, bearer token, request-size and invalid JSON handling | Canonical routes work; obsolete active routes reject; wrong/missing auth fails; 400/401/404/413/422 behavior and sanitized errors remain intentional |
| WRK-03 | Verify worker/backend retry, unreachable service and timeout mapping | Backend responds with documented 502/503/504 or bounded typed failure, no silent success/fallback or duplicated command |
| WRK-04 | Verify worker structural success response validation | Malformed success `document`, `outline`, `references`, `reference_index`, `diff`, `export` and math projection are rejected, not persisted as trusted content |
| WRK-05 | Verify `X-Trace-Id` and request correlation across Al-Bayan, BuTeX and Burhan | Same validated trace ID attached where observable, missing downstream stages clearly marked; no tokens or document bodies in logs |
| WRK-06 | Check worker `/health` service identity and exact candidate binary build | Unsuffixed identity and actual pinned candidate package/worker hash, no mismatch between deployment and imported frontend tarball |
| WRK-07 | Exercise documented maximum payload and output limits | Oversize and malformed input fail gracefully without process crash; bounded diff/validation lists and memory behavior obey documented contracts |
| WRK-08 | Run worker command/error fixtures concurrently against isolated development fixture target | Independent stateless requests do not cross-contaminate documents, IDs, issue lists or trace IDs; no shared mutable document state |
| WRK-09 | Check preserved asset references across worker export and backend storage integration | Exact deduplicated asset IDs, safe storage lookup, no fabricated missing assets or accidental asset deletion |
| WRK-10 | Exercise CLI help, stdin failure recovery and package entrypoint import | Canonical executable and built tarball run without repository-relative source paths; malformed stdin exits/reports structured error as contract requires |

### REV — Persistence, autosave, normal MCP and authoring lifecycle

| ID | Required probe | Expected validation |
| --- | --- | --- |
| REV-01 | Exercise debounced autosave idle and continuous-edit maximum | Coalesced saves are bounded; edits in flight are retained rather than overwritten; latest canonical server document adopted |
| REV-02 | Exercise transient autosave failures and validation error | Expected 2/5/15-second retry schedule (as current baseline), no retry on permanent validation failure, clear user-visible status |
| REV-03 | Exercise stale revision edit conflicts and refresh | Conflicting write leaves authoritative pointer unchanged; client loads latest server base and does not silently discard unsaved local work |
| REV-04 | Exercise hash-based no-op save, typed command no-op and idempotency receipt | No unexpected revision increments, deterministic command receipt/replay behavior |
| REV-05 | Replay a command id with modified payload | Typed conflict/error returned and original immutable revision unchanged |
| REV-06 | Restore prior draft revisions and simulate storage/database failures | Restore adds appropriate new revision; previous snapshot untouched; failure cannot move current pointer or silently commit partial state |
| REV-07 | Exercise retention, history ordering and source revision provenance | History newest-first, lazy detail/summary-first preview, source IDs preserved, referenced assets protected during retention and restores |
| REV-08 | Verify normal MCP authorization, authorship restrictions and revision binding | No cross-user or out-of-scope article modification; agent cannot override document authorship; revision conflicts still enforced |
| REV-09 | Exercise MCP discovery of final canonical typed schema and all supported command variants | Real normal MCP client sees unsuffixed names with correct input/output validation; Developer MCP tests alone cannot satisfy this |
| REV-10 | Run disposable normal MCP → API → saved revision → history restore → browser reopen loop | Correct immutable revisions, content, captions, references, math and image assets survive across independent surfaces |
| REV-11 | Exercise unit registry/used-unit inventory/reverse conversion in retained math documents | Authoritative unit conventions, overrides and affected-token-only updates work; no unit/variable confusion or unauthorized revision update |
| REV-12 | Verify frontend frozen preview used by read/review surfaces | Saved revision preview, manuscript detail and reviewer-facing read-only surfaces remain noneditable and show correct historical content |

### MTH — Standalone math, Arabic typography and compilation

| ID | Required probe | Expected validation |
| --- | --- | --- |
| MTH-01 | Run preserved standalone BuTeX equation editor and MathJax test suites, beyond document tests | All maintained AST/parser, clipboard, caret order, RTL, accent/operator/delimiter, SVG mirror and numeric formatting tests remain meaningful and green |
| MTH-02 | Check MathObject versus RawMathObject persistence and positional nulls | Mixed editable/raw math retains original array/token associations, labels and noneditable status; no silent parser coercion |
| MTH-03 | Check Arabic/English display and editor-session mathematical transformations | Al-Bayan/Burhan projection and actual BuTeX headless adapter agree semantically with no unsupported syntax guessed |
| MTH-04 | Check source provenance of mathematical conversions and diagnostics | Intermediate parse errors and unsupported constructs have typed stage ownership hints, not fabricated browser success |
| MTH-05 | Check SVG MathJax inline/display islands under RTL and LTR preview | No incorrect mirror/reading-order changes, duplicate MathJax registration or browser-only rendering omission |
| MTH-06 | Compile representative two-column, figure, table, citations, Hijri metadata and Arabic/math document | Real XeLaTeX output succeeds in development, captions/labels/RTL and document chrome coherent; PDF source provenance recorded |
| MTH-07 | Check compiler export-safe textual validation and supported font coverage | Unsupported emoji/nonrenderable text explicitly warns/blocks as before; ordinary Arabic, Latin and digits remain allowed |
| MTH-08 | Exercise compile failure and validation/security boundaries | Invalid drafts cannot bypass guarded export/compile; compiler error/log is bounded and revision-bound |
| MTH-09 | Compare exported semantic content with actual compiled PDF and read-only browser preview | Same section order, equations, figure/table identities, citations and Arabic title; explicitly document expected typography differences |

## 4. Cross-checking existing coverage and stress

The final agent must test **all maintained tests**, including (but not limited to) BuTeX `document2_article_meta*`, `document2_block_selection`, `document2_caption_*`, `document2_citations`, `document2_entrypoints`, `document2_equation_dialog`, `document2_extended_commands`, `document2_floats_labels`, `document2_imperative_image`, `document2_json_commands`, `document2_lightweight_preview`, `document2_mobile_workflow`, `document2_persistence`, `document2_provenance`, `document2_reference_*`, `document2_validation*`, `document2_worker_export`, `document2_xelatex_text_validation` and retained standalone math/MathJax/RTL tests. In Al-Bayan include at least `backend/tests/test_butex_worker_client.py`, `backend/tests/test_draft_revisions.py`, `backend/tests/test_used_unit_service.py`, `frontend/src/lib/draft-autosave.test.ts`, `frontend/src/components/dashboard/history-ui-contract.test.ts`, `mcp_server/tests/test_document2_schema.py` (under its new name), `mcp_server/tests/test_draft_tools.py`, relevant Developer MCP tests, and every additional affected test discovered by the source graph. This list is a *minimum anchored inventory*, not an excuse to ignore other touched tests.

Round 7 runs the **full v1 66-ID matrix + all 79 addendum IDs + original v1 stress counts**, with a separate machine-readable report containing one row per ID and an independent source-to-test coverage reconciliation. Repeat the v1 stress loops with these newly listed GUI/mobile/history/error and transport invariants represented where applicable; do not change the v1 iteration counts or weaken its stopping conditions. For any failure, record first observable boundary, uncertainty, stable reproduction fixture, owner and supporting logs/traces; fix code on the two accumulating implementation PR/MR branches, then rerun. Missing Developer MCP connectivity or a missing browser/normal-MCP deployment gives `blocked` or `partial`, not a successful stress result.

## 5. Freeze, versioning and completion rule

- **Immutable original v1:** exact SHA-256 `6457a3d1abe43ba4cde16bd9b287d097978671db5ba3657c28099b1c6e26ca8e`. This file and its original 66 IDs are unchanged by the addendum.
- **Immutable addendum A:** record and verify its exact SHA-256 in both plans after committing identical copies. A matching Git blob is supplemental evidence, not a substitute for content hash.
- **After Phase 0:** neither file may be edited in place in Rounds 1–7. A true error/omission needs separately reviewed versioned addendum B or v2, explicit owner decision and a recorded change to final expectations. Observed failures do **not** justify rewriting the oracle.
- **Round 0 shared completion:** owner sign-off on v1 plus addendum A, identical content fingerprints in both repos, coherent matched eight-round plans, no claimed test passes. The owner has authorized marking Round 0 complete on 2026-10-21; this **does not** mean the migration implementation or final acceptance suite has passed.
- **Round 7 final completion:** all 145 mandatory IDs passed, all retained relevant baseline test cases accounted for, original stress requirements passed, both plans/round ledgers aligned, and an independently reviewed release-readiness decision. No automatic merge, npm publish, tag, production deploy or production test follows from this document.
