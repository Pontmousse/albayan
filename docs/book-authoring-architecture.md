# Book authoring in Al-Bayan — architecture, contracts and phased delivery

> **Status:** proposed; no book feature is implemented as of 2026-10-18. **Baseline:** `Pontmousse/albayan` `develop` at `dc17ecb` and BuTeX `7.4.2`. **BuTeX counterpart:** [book-editor-plan.md](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md). Types/endpoints in this document are **design proposals**, not shipped contracts.

## 1. Product goal and v1 boundary

Enable users to author a long Arabic scientific book or thesis as individually editable chapters, with front matter, appendices, globally resolved citations/labels, chapter-aware numbering, generated TOC, and reproducible whole-book PDF. Users and AI agents edit the **same authoritative draft**, with immutable history and conflict detection; authors retain control over destructive actions and final delivery.

**V1 is an authoring/export feature.** Do not silently re-use article peer review, editorial assignments, journal publication, ISBN or a book distribution workflow. A later phase may add a distinct `BookEdition`/submission policy after explicit editorial requirements. Article editing and `ArticleVersion` remain unchanged.

**Explicit non-goals:** writing a second editor or math parser; storing LaTeX as canonical text; editing all chapters as one huge mutable document; hosting a compiler inside MCP; collaborative CRDT; institution-specific thesis templates, `\\part`, bibliography processors beyond the existing BuTeX reference model; editing a live submitted book.

## 2. Observed current code (not proposed)

- The article domain uses `Article`, immutable `ArticleDraftRevision`, `ArticleVersion` (formal submitted snapshots), and `DraftCommandReceipt`. See `backend/app/models/article.py`, `backend/app/services/article_draft_service.py` and [2026-09-15-draft-revision-architecture.md](superpowers/specs/2026-09-15-draft-revision-architecture.md). The old `ArticleSession` layer is **retired**.
- Current browser editor is `ButexDocumentEditor2` from `@drghaliasri/butex/react-document2`; autosave is revision-aware (`frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`). These are **article** flows, not a book implementation.
- Current `butex_document2` worker is private and stateless; FastAPI calls its normalize/outline/commands/export and references/index/diff operations. Current worker export makes an **article**. MCP is a thin authenticated FastAPI facade, never a direct worker/S3 client.
- FastAPI currently converts permitted canonical LaTeX math tokens through Burhan and persists the resulting structured MathObject via Document2 command application; equation mappings and unit conventions are article-scoped.
- Compilation currently passes one `tex` string and optional assets to `/xelatex/render`; the article preview is bound to an exact immutable draft revision. The current article compiler limit of 50 assets and document worker payload limit must **not** be adopted as book limits without redesign.
- No book-specific database model, API route, React book editor, book worker or book-specific MCP tool was found in `develop`.

**Architectural rule:** learn from the article revision model and existing typed Document2/Burhan pipeline; do not copy retired article sessions or the August 2026 single-`document.json` storage instructions.

## 3. Component ownership and end-to-end path

```text
browser (BuTeX BookEditor)     AI agent (small, typed book MCP surface)
            |                           |
            +---------------------------+
                         |
                Al-Bayan FastAPI
         auth, permissions, command IDs, CAS
         book + unit revision history, S3 assets
              |                         |
       BuTeX document2 worker    BuTeX book worker
         unit block commands     manifest, catalogs,
         and normalization       validation, export bundle
              |                         |
              +-------------+-----------+
                            |
         canonical immutable book revision
        manifest + references + pinned unit JSON
                            |
                  trusted compiler
           multi-file XeLaTeX + assets
                            |
                    immutable PDF/log
```

BuTeX is the single owner of `BookManifestJson`, `BookReferencesJson`, `BookSnapshotJson`, book command vocabulary, global reference/label resolution, generated content, numbering and deterministic `BookLatexBundle`. Al-Bayan must **mirror/validate** published schemas rather than invent a competing serialization. In the browser, mount one book-content Document2 editor at a time. BuTeX never fetches from S3 or authenticates a user.

For mathematical commands, retain:
```text
AI canonical interoperable LaTeX
 -> Al-Bayan typed book-unit Document2 command
 -> FastAPI + Burhan (book-scoped notation/unit conventions)
 -> structured MathObject -> existing Document2 worker
 -> immutable unit + book revision -> BuTeX editing/MathJax
```
Do not send raw unsupported LaTeX to the book worker as a shortcut or duplicate Burhan's conversion in BuTeX. A book agent must still discover `get_math_authoring_capabilities` first.

## 4. Proposed persistence (book root snapshots, independent unit revisions)

Use **separate book entities** initially, not a risky polymorphic rename of every `Article` table:

| Relational entity | Purpose |
| --- | --- |
| `Book` | Creator, metadata/ownership, draft status, `current_book_revision_id`, monotonic `book_revision_number`, shared math/notation policy |
| `BookUnit` | Stable book/unit relation, authorable unit identity; current order/type come from the manifest in current book revision |
| `BookUnitRevision` | Immutable per-unit canonical `Document2Json` object key/hash, actor/provenance, unit revision number, ancestry |
| `BookRevision` | Immutable aggregate root: manifest version, references revision, **exact mapping** `unit_id -> BookUnitRevision.id`, metadata and revision hash |
| `BookCommandReceipt` | Idempotent book structure/reference and unit command results, including request fingerprint and resulting revision |
| `BookCompileAttempt` | Attempt identity, exact `BookRevision`, status/log/PDF keys; no stale/current PDF confusion |

Revision storage keys are **never overwritten**, and the root references only immutable objects. Example conceptual S3 layout (subject to phase-0 contract):

```text
books/{book_id}/draft/units/{unit_id}/revisions/{unit_rev_id}/document.json
books/{book_id}/draft/book-revisions/{book_rev_id}/manifest.json
books/{book_id}/draft/book-revisions/{book_rev_id}/references.json
books/{book_id}/draft/book-revisions/{book_rev_id}/snapshot.json  # references unit IDs/hashes/keys; not duplicated bodies
books/{book_id}/draft/assets/{asset_id}
books/{book_id}/previews/{book_rev_id}/{compile_id}/compiled.pdf
books/{book_id}/previews/{book_rev_id}/{compile_id}/compile.log
```

`BookRevision` roots are the immutable consistent **view of a whole book**, while `BookUnitRevision` objects avoid duplicating N chapters every time a sentence changes. An optional DB cache of active unit heads is derived/transactionally synchronized with the current book root; it is not another authoritative mutable document.

**Concurrency rule:**
1. Unit editing supplies `unit_id`, `base_unit_revision`, `command_id`, and one typed `Document2Command`. FastAPI checks the current unit pointer under a short book-level transaction, loads the immutable unit, transforms via Document2, and commits a new unit revision + new book root atomically as far as PostgreSQL pointers are concerned. Immutable S3 objects may be written before the transaction; unreferenced failed candidates are garbage collected.
2. Edits to **different** units may succeed concurrently if the target unit's base revision still matches, even if the book root advanced. Edits to the **same** unit return a 409 with the authoritative current unit/book revision. No silent lost updates.
3. Structural reordering/add/delete, shared reference edits, book metadata or global notation settings use an exact `base_book_revision` CAS; conflict requires reload/reconciliation.
4. A no-op need not make a new revision. Retry using the same `command_id` returns the same result, not a duplicate operation. Existing article permission/provenance ideas apply, but book actor authorization is enforced independently.
5. Restoring a unit creates a **new** immutable unit revision + book root without overwriting unrelated current chapters. Restoring a whole book creates a **new** root from a historic snapshot; never mutate or rewind history. Retention/asset pruning **must pin** all units/assets referenced by retained book roots, compile attempts and any formally frozen edition.

Every full preview/export must materialize **one specified BookRevision**, not whichever chapter heads happened to be current during a multi-request read. Book structure can be reordered without changing unit identity or corrupting citations.

## 5. Domain, reference and asset rules

- Book manifest groups are `frontmatter`, `chapters`, `appendices`, `backmatter`; editable units each contain canonical `Document2Json`; generated title page, TOC, figure/table lists and bibliography are **not** fake units. BuTeX's [versioned v1 contract](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md) is authoritative for exact field names.
- `Book` owns shared `references.json`, citation keys and book-wide labels; individual chapter `references` must be empty and chapter-local bibliography must fail validation. The book shell/editor receives the global catalog read-only. Citation and cross-reference resolution reports duplicate/unresolved keys with unit location.
- Equations stay structured. Book-scoped notation mappings and unit conventions feed the **existing FastAPI/Burhan** conversion used by every unit. Changing these settings creates a book root revision; ensure math authoring uses those same settings and the published round-trip-safe syntax. A preview/export always captures the matching settings revision.
- Book-scoped assets use stable opaque IDs; ensure permission checks on each upload/read, unit provenance for diagnostics, and collision-free safe output file names. Reorder must not break image IDs. Prevent deleting any asset pinned by revision history, an immutable edition or an active compile. Do not hard-code article's 50-asset cap for a book.
- Shared authorship/roles are a **book-domain** policy; do not mistake `Document2.meta.authors` in a chapter for verified platform authors. For V1 keep author-owned edits, then design collaborator/editor access only after explicit review.
- Version 1 focuses on Arabic RTL source and output, using the existing XeLaTeX/BuTeX mathematical direction behavior and Arabic-aware numbering.

## 6. Proposed API and MCP boundary

These are **suggested route shapes**, not available endpoints. Add FastAPI routes guarded by book-specific scopes/permissions; mirror BuTeX's schemas at typed boundaries.

| Route | Responsibility |
| --- | --- |
| `POST /api/v1/books`, `GET /api/v1/books/me` | New book and book list |
| `GET /api/v1/books/{id}/draft` | Latest book metadata + root revision IDs; optional bounded materialized snapshot |
| `GET /api/v1/books/{id}/draft/outline` | Ordered units/headings, stable IDs, current revision |
| `GET /api/v1/books/{id}/units/{unit_id}/draft/blocks` | Compact unit content/IDs + unit revision for editing |
| `POST /api/v1/books/{id}/units/{unit_id}/draft/commands` | One Document2 command, idempotent and unit-CAS |
| `POST /api/v1/books/{id}/draft/commands` | Book structure/metadata/shared-reference command, book-CAS |
| `GET /api/v1/books/{id}/draft/revisions` | History, revision-bound inspection/restore (restore human-only in V1) |
| `POST /api/v1/books/{id}/draft/compile` | Compile the **current exact book root** on explicit request |
| `GET /api/v1/books/{id}/draft/compile/status`, `GET .../pdf` | Show/retrieve attempt only when it matches the requested revision |

Browser autosave may use a dedicated `PUT /units/{unit_id}/draft` endpoint, analogous to articles, but **never bypass** unit revision/CAS invariants. A book structure command must not go to the document2 worker; a unit text command must not go to the book worker.

For agents, start with **four task-oriented book tools** (plus existing reusable math capability discovery): `list_books`, `get_book_outline`, `get_book_unit_blocks`, `apply_book_unit_command`. Add `apply_book_structure_command` when structured book edits are safe, and compile/status/PDF only when whole-book compilation is implemented. Prefer a scoped book resource/schema to dumping all chapter JSON in tool results. Agents must never create arbitrary stable IDs, bypass user approval for formal submission/publication, or call private workers directly. Keep book tools distinct from article tools to preserve a clear authoring goal.

## 7. Multi-file export/compile contract

The current compile pipeline uses **one** TeX source string. Books need a distinct server-side bundle adapter:
1. Lock an immutable `BookRevision`, materialize all pinned unit JSON + shared references from S3, and call stateless BuTeX BookWorker `validate` + `export`.
2. Receive deterministic `BookLatexBundle`: `main.tex`, style and unit `.tex` files, typed required assets, warnings/diagnostics, content/hash identity. Reject unsafe paths, duplicate keys/labels and unresolved cross-unit required references according to the agreed validation policy.
3. FastAPI maps asset IDs to safe bundle files, authorizes materialization, and hands the entire text-file map plus binaries to a **new/extended trusted compiler contract**. Do not assume current `/xelatex/render` accepts `\\include` or ZIP or new files; design/test a separate multi-file contract with the compiler service first.
4. Run XeLaTeX as many bounded passes as needed for TOC, figure/table lists, bibliography and cross-references. Store compile logs, exact root/attempt ID, and final PDF immutably.
5. Serve PDF only when its `BookRevision` matches the requested current or historic revision; editing any unit invalidates *current* freshness, but never deletes previous immutable previews.

Test a realistic long book and define body/asset/time limits **independently** from the 5 MiB Document2 worker and 50-asset article implementation.

## 8. Recommended staged implementation (two repositories)

| Phase | BuTeX owner | Al-Bayan owner | Release gate |
| --- | --- | --- | --- |
| **0. Cross-repo contract** | Fix versioned schema, content mode, book commands, diagnostics/export bundle, worker limits | Fix DB root/unit revision model, CAS, permission + API contracts and compiler bundle protocol | Shared golden fixtures; no ambiguity about source of truth |
| **1. Document2 unit reuse** | Content-only export/preview, external catalogs, heading labels, transaction guard | Standalone unit editor/spike with structured math conversion and existing image handling | Article workflow regression tests green; no article chrome/bibliography in unit |
| **2. Book persistence + core** | Manifest validation, outline, global refs/labels, numbering and book commands | Books/units/root history, immutable object storage, unit and book CAS, per-unit autosave/restore, asset authorization | Two simultaneous different-unit edits both safe; stale same-unit edit returns 409; historical snapshots reproduce exactly |
| **3. Book UI and agent authoring** | Single-active-unit `ButexBookEditor`, navigation, shared references, full preview | Dashboard routes, save status/conflicts, minimal book MCP, Burhan notation/unit policy | Human+agent edits visible in same history; navigation cannot lose dirty math/text |
| **4. Export + compile** | Deterministic multi-file `book2Latex` + stateless `butex-book` API and tests | Materialize exact book revisions, multi-file compiler integration, PDF/log history, download | Multi-pass Arabic PDF, TOC/cross-chapter citations and assets match browser preview |
| **5. Hardening and optional editorial future** | Performance, package release, docs, demos, safe large book cases | Permission/security load tests, monitoring, lifecycle QA; **separate later decision** on submitted book editions | End-to-end dev browser/normal MCP checks pass; book authoring ready without weakening articles |

BuTeX phases 1-4 can land incrementally in its own `develop`. Al-Bayan may prototype storage ahead of full book UI, but must not publish a book workflow before the shared contracts and acceptance gates pass. No deployment or production changes are authorized by this document.

## 9. Acceptance checklist

- Three or more Arabic chapters, front matter, an appendix and one generated TOC/bibliography.
- Shared citations, cross-chapter equation/figure/table/heading references and stable numbering after reorder; deterministic duplicate/unresolved diagnostics.
- Normal BuTeX editing including structured Arabic math (Burhan pipeline), inline citations, images/tables and unit-level undo/redo.
- Browser navigation while dirty/while an equation drawer is open; no lost edits or stale image-picker effects.
- Independent unit autosave, repeat command-id idempotency, 409 conflict handling, full historical restoration, structural CAS and immutable hashes.
- Compiled PDF generated from the exact frozen root with repeated XeLaTeX passes; asset scoping/collision/path validation and logs.
- Browser vs headless preview/export parity; standard **Al-Bayan normal MCP** tested, not Dev MCP success alone.
- Existing article create/edit/submit/review/PDF/MCP behavior unchanged. No production writes.

## 10. Documentation authority and cleanup

This file is **the current Al-Bayan book integration plan**. The BuTeX GitLab book plan is **the current library/worker contract**. The old August `docs/afkar-al-mashrou.md` §2 narrative about BuTeX `^5.6.1`, manual save, one mutable document and planned S3 paths was superseded and should be reduced to a pointer here; preserve the unrelated ideas/tutorial/notification sections. Historical pre-cutover docs on article sessions are **not current runtime instructions**; rely on the September 15 immutable revision specification and live code. The historical rename audit may refer to old BuTeX files as historical references, not current Al-Bayan files.
