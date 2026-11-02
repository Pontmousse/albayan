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

## 6. Multi-writer concurrency and a unified write pipeline

**Target scenario:** four coauthors actively edit one article, each potentially running one or several agents (e.g., a prose agent, a bibliography agent, and a math agent). The architecture must support **N concurrent writers**, not just one browser versus one MCP caller. An author may also open several tabs. The concurrency semantics should be **independent of who or what submits an edit**; permissions and provenance must still distinguish humans, delegated agents, and trusted service operations.

### 6.1. N writers do not require a combinatorial N-way merge

The article needs **one canonical, ordered sequence of committed revisions**, even if many candidate edits are in flight. For example, suppose four authors and eight agents all start from revision 100. The database currently permits only the first successful candidate to create revision 101; other candidates based on 100 receive 409 unless retried. A future reconciler should validate each remaining candidate against the *latest committed document* and, if independent, commit it as revision 102, 103, etc. The order is serialization order, **not** evidence that writers were editing sequentially.

- Apply the same three-way principle repeatedly: **writer's base + writer's intended changes + current authoritative draft**. There is no need to compare all pairs of authors/agents or construct a giant twelve-way merge.
- The server revalidates targets, ancestors, ordering anchors, references, assets, metadata, math mappings, and unit conventions after every rebase. **Disjoint IDs are useful but not sufficient** to prove independence.
- Operations against the same element, delete-versus-edit, conflicting moves/anchors, renaming a reference while another writer uses it, or changing equation conventions may still require a precise conflict. No automatic semantic winner, priority based solely on "human"/"agent", or silent last-writer-wins.
- A busy article may produce many accepted short revisions, but two genuinely simultaneous writers of the **same text span** require Level 3B (or a manual resolution), not just Level 2. Level 3A makes independent committed changes visible promptly but does not synchronize every keystroke.

**Assessment:** Level 2 is feasible for four authors plus their agents *when edits are structurally independent*; writer count mainly increases contention, revision churn, permissions/audit requirements, and the probability of overlapping edits, rather than changing the fundamental merge algorithm.

### 6.2. Centralize the write *authority*, not necessarily every editor interaction

**Partly implemented already:** browser `PUT /draft` (whole `DocumentJson`) and MCP `POST /draft/commands` (one typed command) both reach `article_draft_service.create_revision`, which normalizes through BuTeX and enforces the final revision check. The current **input formats and conflict/recovery policies differ**, however. Simply calling the same save function is not yet a unified collaboration protocol.

**Proposed logical write path** (a design direction, **not** a shipped endpoint):

```text
Human browser(s)     Human-owned MCP agent(s)     Trusted service jobs
        \                     |                         /
         \  authorized editing intent (operation / patch / snapshot)
          \                   |                       /
           Al-Bayan single authoritative draft-write service
             authenticate + authorize actual actor and delegation
             identify request + base revision + affected semantics
             canonicalize/validate through BuTeX; Burhan for math input
             reconcile or report precise conflicts against latest draft
             atomic article-level compare-and-swap + immutable revision
             record provenance; optionally notify active subscribers
                              |
                     canonical Document2 draft
```

Recommended **one contract in principle**, with multiple compatible input forms rather than forcing every client to produce the same low-level event:

- **Scoped intents preferred:** a BuTeX Document2 command or an equivalent identity-aware patch for one block, field, table cell, reference or semantic operation. MCP already supplies typed commands. These give the best merge opportunities.
- **Browser transition:** BuTeX currently emits complete JSON for autosave; keep that supported initially, but interpret it against its known base as a conservative three-way change. Later, expose incremental document transactions/patches from BuTeX for browser edits **when they preserve composition, caret, undo/redo, Arabic text and equation behavior**. Do not immediately translate each keystroke into a persistent revision.
- **Whole-document replacement retained as an explicit fallback/import operation**, not treated as equivalent to a targeted edit. It needs strict base checks or safe three-way reconciliation; never replace remote changes because a client presents a newer revision number.
- **Common server guarantees:** caller-independent CAS, idempotency, validation, revision creation, conflict shape, authorization, safe submission/freeze boundaries, audit and post-commit notifications. Adapters for HTTP/normal MCP should stay thin; no second revision engine in MCP or the browser.
- **Idempotency detail:** currently typed MCP commands have `command_id` receipts, while browser PUT does not use the same receipt path. The current command request hash **includes `base_revision`**; a client must not silently reuse an ID with a mutated base/payload after a 409. A future unified operation identity/rebase policy must specify safe retries without duplicate application.

A unified *logical* write service does **not** require a single global process/queue or giant mutex across all articles. Keep per-article serialization using the existing database locking boundary; consider batching, scheduling, or backpressure per busy article only if measurements justify it.

### 6.3. Multi-author access, delegated agents, and reliable attribution

The existing `ArticleAuthor` table supports multiple users linked to one article, and draft access currently checks that link. **This does not establish that the product has a complete collaborator invitation, editing-role, or ownership-transfer workflow.** Academic authorship/credit is not necessarily identical to edit authorization: investigate explicit owner, coauthor-editor, read-only, invited contributor, and submission authority separately before promising four-user collaboration.

Current `Actor` differentiates human vs agent, associates agent credentials with a user, and enforces scopes; an agent acts **on behalf of an authorized user**, not as a separate unrestricted article owner. The service currently stores `created_by` (user UUID) and `actor_type` in each revision, but not the `Actor.token_id` or a distinct agent/session identity on the revision. Several agents belonging to one author can therefore be indistinguishable in draft-history provenance. A future design should preserve server-derived **user, delegation/agent identity when available, originating client/session, operation ID, reason, and exact affected content**—without trusting unverified client labels. OAuth agent identity may require a different trusted identifier from local API-token identity. Humans and agents share conflict rules **but not privileges**: retain agent scope checks, restrictions on author metadata/history restore, and human-only submission/approval policies.

**Migration implications:** the basic multi-writer CAS/merge prototype may need **no DB migration**; existing `ArticleAuthor` and immutable revisions are usable. A full invited-collaborator permission model, durable agent-level provenance, or reliable event outbox will **likely require additive schema changes**. Do not conflate a coauthor's academic authorship position with edit permissions.

### 6.4. Multi-writer scaling risks and explicit acceptance cases

- **Global per-article revision contention:** more clients reading revision N means more stale submissions. Retry only boundedly with fresh validation and a conflict exit; avoid tight retry loops/starvation. The per-article serial commit order remains essential even if reconciliation runs in parallel.
- **Revision retention and undo:** current retention is **100 snapshots per article**. Many autosaves/agents can exhaust that history rapidly, stranding stale bases and weakening practical undo/recovery. Evaluate coalescing, checkpoint frequency, and retention policy before encouraging high-frequency collaborative writes.
- **Object-storage cost and orphans:** `create_revision` currently normalizes and writes a candidate S3 object **before** acquiring its final DB row lock; losing the CAS race can leave a candidate object without a committed revision. An orphan cleanup script exists (`backend/app/jobs/cleanup_draft_orphans.py`), but its **scheduled operation was not verified**. Assess write amplification, cleanup guarantees and retention under contention before scaling.
- **Cross-element invariants:** citation/reference keys, labels, image assets, table structure, document metadata, unit conventions, equation mappings and structured math may couple ostensibly separate edits. Normalize/validate the *combined* result rather than trusting merely disjoint block IDs.
- **Trust and lifecycle:** an agent's write must not gain extra authority by passing through a common service. Submission and compilation pin an exact immutable revision and must remain consistent with new writes, live sessions, and freezes.
- **Validation fixture:** simulate **4 authors + 8 distinct agent clients**, starting with the same base; mix independent paragraph/reference/math changes and deliberate collisions. Verify accepted changes are all present exactly once, each revision has correct ordering/attribution, conflicts never drop unsaved work, unauthorized agents cannot edit, retransmission is idempotent, stale/expired bases fail safely, and the compiled result matches the final canonical document. Include failures during S3 writes, transaction races, reconnect, and repeated rapid autosave.

**Recommended sequencing:** first prove N-writer safety using the existing immutable revision/CAS service and the Level 2 three-way merge prototype; then expose live updates in Level 3A; only explore Level 3B's same-field concurrent typing after BuTeX can apply remote operations without corrupting local cursor, history or equation state. Keep **all** of this future work outside Level 1 PR #249.

## 7. Delivery order and acceptance gates

1. **Ship Level 1 separately:** regression-test 409 recovery, verify in the authenticated DEV browser (including two tabs and MCP/browser contention), then merge PR #249. No merge functionality or migration in the Level 1 code path.
2. **Level 2 prototype:** prove `B/L/R` deterministic merges for independent blocks and correct rejection for collisions. Test mixed human PUT and MCP commands, math/citations/tables, legacy IDs, stale bases, revision retention and server races. Validate normalization, source attribution, revision history and compile output.
3. **Level 2 product integration:** add narrow API and UI behavior behind an opt-in development gate; present exact conflicts instead of a document-wide overwrite choice when possible.
4. **Level 3A:** add revision notifications and remote-update application while preserving unsaved text, cursor, undo/redo and equation sessions; exercise reconnect/out-of-order events and permission failures.
5. **Level 3B only if usage supports it:** prototype one collaboratively edited paragraph with BuTeX, then separately test math, nested blocks, tables, offline recovery and consistency before committing to infrastructure.

**Non-goals for this document:** designing new API schemas, approving migrations, implementing CRDT, modifying Burhan, changing production infrastructure, or proposing that AI automatically resolves true semantic conflicts.

## 8. Recommendation

Prioritize **Level 2 plus Level 3A**, especially for **human–MCP agent collaboration**. This captures most of the near-term benefit (independent edits in one article without interruption) while preserving the existing Document2, immutable revision, authorization and compilation boundaries. Reassess full Level 3B only after measuring real usage and proving a safe editor synchronization model.

**Environment/status note:** Findings above are based on source inspection on `develop`; no new implementation, browser end-to-end verification, CI run or performance benchmark was performed for Level 2/3.
