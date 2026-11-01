# Collaborative authoring after autosave conflict safety — feasibility study

> **Status: EXPLORATORY FEASIBILITY STUDY — NOT APPROVED OR IMPLEMENTED.** Reviewed against current source on 2026-11-01. This note accompanies [Al-Bayan PR #249](https://github.com/Pontmousse/albayan/pull/249) (Level 1, issue #248) for future planning only. **Merging PR #249 does not authorize or implement Level 2 or Level 3.**
>
> **Scope:** Article draft editing across browser and normal MCP. No code, schema, deployment, or data change is requested by this proposal. Estimates below are qualitative architecture judgments, not validated prototypes.

## 1. Motivation and boundaries

The existing autosave uses optimistic concurrency: a browser uploads a complete `DocumentJson` with a `base_revision`; an MCP agent uses a typed `DocumentCommand` with its own `base_revision`. If another writer advances the authoritative article revision, the stale writer receives HTTP 409. This is intentional protection against silent overwrites. The conflict window is **not** limited to the autosave debounce interval: a tab can remain stale after any external update.

**Level 1 (PR #249)** protects unsaved browser work on a 409 and offers explicit recovery choices. It **does not** reconcile independent edits. Selecting the local copy can still replace newer, unrelated remote changes. Level 1 should be independently reviewed and merged as a safety fix before any collaboration redesign.

The desired future behavior is: a human can edit paragraph P7 while an MCP agent updates equation E4, with both changes retained automatically when safe, and a precise conflict shown only for overlapping edits.

## 2. Observed implementation (not proposals)

| Area | Observed implementation | Consequence |
| --- | --- | --- |
| Al-Bayan draft model | `ArticleDraftRevision` stores immutable revision metadata, canonical document hash, storage key and actor provenance; `Article` records the current revision; snapshots live in object storage. | Durable history and a common base for three-way reconciliation already exist. |
| Backend concurrency | `article_draft_service.create_revision` checks `base_revision` and rechecks under a PostgreSQL row lock; both HTTP PUT and MCP commands ultimately create canonical revisions. | Preserve this authoritative compare-and-swap boundary for every merge. |
| Browser | `frontend/src/lib/api/articles.ts` sends whole-document PUT; `draft-autosave.ts` owns debounce/retry/conflict handling. | Browser edits need document-level three-way comparison or a new operation protocol. |
| Normal MCP | `apply_draft_command` sends one typed operation, a unique `command_id`, and a base revision to FastAPI. | Targeted commands are more readily revalidated/rebased than whole-document PUT. |
| BuTeX Document2 | `DocumentJson` has stable block, field, token, list-item and table-field identities (some optional for legacy documents); typed commands support targeted edits. | Structural merge is plausible, but identity stability and normalization must be tested. |
| BuTeX diff | `diffDocument` yields bounded textual JSON-change chunks and intentionally excludes identity sidecars. | Useful for review/summary; **not** a complete patch or a semantic merge engine. |
| BuTeX React editor | The editor maintains its own document state, undo/redo, selections and equation sessions. Changing `initialDocument` resets state/history. | Live remote updates cannot simply replace `initialDocument` while someone is typing. |
| Draft retention | `REVISION_RETENTION_LIMIT = 100` in `article_draft_service.py`. | A base revision may expire; failed or missing-base merges must never silently overwrite. |
| Access | Current editable drafts are authorized through article authorship. | Multiple human collaborators need an explicit permission model, not merely presence/sockets. |

Relevant code: `backend/app/models/article.py`, `backend/app/services/article_draft_service.py`, `backend/app/schemas/document.py`, `mcp_server/src/albayan_mcp/tools/drafts.py`, `frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`, and BuTeX `src/document/{types,jsonCommands,diff}.ts`, `src/react-document/ButexDocumentEditor.tsx`.

## 3. Level 2 — conservative structural reconciliation

**Feasibility: high; effort/risk: moderate.** Build on the existing revision and Document2 model rather than introducing realtime infrastructure.

A three-way merge compares **base B**, **local candidate L**, and **current remote R**. Using stable identities, it can accept non-overlapping edits and reject ambiguous ones:

- **Initially safe candidates:** editing different existing blocks; adding a distinct block at an unambiguous anchor; updating different independently addressable table cells or metadata fields *only after proven safe*.
- **Require conflict:** both parties edit the same text field/equation; delete-versus-edit; incompatible moves/inserts at the same anchor; overlapping table restructure; incompatible reference/label changes; equation-mapping or unit-convention changes that affect interpretation.
- **Do not use revision `affected_block_ids` alone as a proof of non-overlap.** The current helper tracks direct targets and new top-level blocks; it is not a comprehensive write-set for nested content, metadata, references or side effects.
- **Equations remain atomic in v1:** merge changes to different equation tokens or blocks if proven independent, but never mechanically splice two concurrent changes inside one structured `MathObject`.

**Suggested ownership:**

1. **BuTeX (preferred):** a pure, deterministic, identity-aware `mergeDocument(base, local, remote)` contract returning either canonical merged JSON plus a structured conflict list, or conflicts without a merged output. Keep document command semantics, normalization and identity checks in BuTeX. A narrow first prototype could live in Al-Bayan, but avoid growing a second Document2 implementation in Python.
2. **Al-Bayan FastAPI:** load the base/current snapshots, authorize, ask BuTeX to reconcile, re-check the current revision **under the existing transaction lock**, retry if a newer revision appeared, then persist exactly one immutable canonical revision with correct attribution. No unsafe last-writer-wins fallback.
3. **Browser:** retain local edits during conflict; attempt safe reconciliation; offer a focused human decision only for unresolved changes. Keep an unsaved-work guard until the merged revision is confirmed.
4. **MCP:** optionally revalidate/replay an individual stale targeted command against the latest revision when the target/anchors remain valid, using the existing command-ID idempotency semantics. Never replay blindly; keep precise conflict errors.

**Database migration:** **not required for an initial implementation.** The existing immutable base/current snapshots and revision records are sufficient if their base remains retained. A future explicit merge parent or audit provenance may justify additive metadata, but should not be a prerequisite.

**BuTeX changes:** likely **small to moderate**, limited to a pure semantic merge/operation analysis facility and tests. Existing diff cannot be reused as-is. **Burhan changes:** **not expected** for atomic equation handling; still verify canonical math round-trips and article equation/unit mapping consistency.

**Main risks:** incomplete/unstable IDs in legacy material, normalized representations changing spuriously, identity collisions, cross-document references, nested edits, stale base pruning, races between merge computation and commit, and accidental replacement of human/agent content. Accept conflicts rather than guess.

## 4. Level 3A — live revision awareness (incremental collaboration)

**Feasibility: high after Level 2; effort/risk: moderate.** Publish a lightweight article-revision event **only after a successful committed revision**, and have open editors fetch/reconcile changes immediately. SSE or WebSockets can transport notifications; the authoritative document remains in FastAPI/object storage, **not** in an untrusted client event.

- Receive notifications for browser and MCP revisions; deduplicate and tolerate out-of-order/missed events; re-fetch canonical state after reconnect.
- Apply safe incoming changes **without resetting the BuTeX editor's local draft, focus or undo history**. This likely requires a targeted BuTeX editor API even if backend merge logic is complete.
- Use existing revision numbers as ordering checkpoints; do not imply Google Docs-style simultaneous keystroke merging.
- Authenticate each subscription, enforce per-article read access and avoid leaking manuscript content through presence/events.

**Database migration:** potentially **none** if events are ephemeral and the existing revision history remains the recovery source. If durable delivery or replay becomes necessary, an outbox/event table may be warranted. **BuTeX:** likely a targeted remote-patch/rebase integration. **Burhan:** generally none.

A sensible product result is: an agent changes one equation while a human writes elsewhere, and the new content appears without losing the human's in-progress edits.

## 5. Level 3B — true simultaneous editing

**Feasibility: technically possible; effort/risk: high.** Shared cursors, live same-paragraph typing, offline edits and smooth reconciliation require a collaborative transaction model (OT or a CRDT such as Yjs) plus a transport/server.

This is **not** just adding WebSockets:

- BuTeX currently owns local React editor state, history, cursor/selection and math sessions. It would need substantial collaborative-state integration or an adapter that maps synchronized operations to/from Document2 without corrupting identities and source semantics.
- Keep **canonical Document2 JSON** as the persisted, compiled, revisioned source of truth. Define carefully when an in-memory shared session becomes a durable immutable revision, and how submissions/compilation pin an exact consistent snapshot.
- Treat equations as atomic collaboration units initially; concurrent character-level editing within a math AST would expand risk across BuTeX and Burhan unnecessarily.
- Define authorization, roles, presence, heartbeat, reconnection, offline replay, session expiry, rate limits, multi-instance scaling, and audit provenance.
- Avoid storing every keystroke as a full immutable revision; separate ephemeral operations from durable checkpoints.

**Database migration:** **likely** for persisted collaboration sessions, op-log/checkpoint references or resumable state, although transient presence could live in Redis. Deployment/infrastructure would also change. **BuTeX changes:** substantial. **Burhan changes:** not inherently required unless collaborative editing of equation internals is later introduced.

Full CRDT adoption should **not** be committed to before a focused BuTeX editor proof of concept validates undo/selection behavior, canonical round trips and compilation consistency.

## 6. Delivery order and acceptance gates

1. **Ship Level 1 separately:** regression-test 409 recovery, verify in the authenticated DEV browser (including two tabs and MCP/browser contention), then merge PR #249. No merge functionality or migration in the Level 1 code path.
2. **Level 2 prototype:** prove `B/L/R` deterministic merges for independent blocks and correct rejection for collisions. Test mixed human PUT and MCP commands, math/citations/tables, legacy IDs, stale bases, revision retention and server races. Validate normalization, source attribution, revision history and compile output.
3. **Level 2 product integration:** add narrow API and UI behavior behind an opt-in development gate; present exact conflicts instead of a document-wide overwrite choice when possible.
4. **Level 3A:** add revision notifications and remote-update application while preserving unsaved text, cursor, undo/redo and equation sessions; exercise reconnect/out-of-order events and permission failures.
5. **Level 3B only if usage supports it:** prototype one collaboratively edited paragraph with BuTeX, then separately test math, nested blocks, tables, offline recovery and consistency before committing to infrastructure.

**Non-goals for this document:** designing new API schemas, approving migrations, implementing CRDT, modifying Burhan, changing production infrastructure, or proposing that AI automatically resolves true semantic conflicts.

## 7. Recommendation

Prioritize **Level 2 plus Level 3A**, especially for **human–MCP agent collaboration**. This captures most of the near-term benefit (independent edits in one article without interruption) while preserving the existing Document2, immutable revision, authorization and compilation boundaries. Reassess full Level 3B only after measuring real usage and proving a safe editor synchronization model.

**Environment/status note:** Findings above are based on source inspection on `develop`; no new implementation, browser end-to-end verification, CI run or performance benchmark was performed for Level 2/3.
