# Design: Replace article sessions with immutable draft revisions

**Date:** 2026-09-15  
**Scope:** Albayan article authoring, autosave history, MCP editing, preview compilation, submission/versioning, and draft storage.  
**Status:** Proposed architecture for phased implementation.  

---

## 1. Decision

Replace the current `ArticleSession` working-copy model with one persisted draft-history model:

```text
Article
│
│ current metadata + workflow state
│ current_draft_revision_id
│
├── DraftRevision 1
├── DraftRevision 2
├── ...
└── DraftRevision 57      ← current editable draft

            submit
              │
              ▼
      ArticleVersion v1   ← immutable formal submission
              │
            review
              │
       revisions requested
              │
              ▼
      more DraftRevisions
              │
           resubmit
              │
              ▼
      ArticleVersion v2
```

The permanent semantic distinction is:

> **`ArticleDraftRevision` is an autosaved/reversible state while authors and agents are editing.**

> **`ArticleVersion` is an immutable manuscript snapshot that crossed a formal journal workflow boundary.**

Do **not** turn `ArticleVersion` into autosave history.

Do **not** preserve a second editable `ArticleSession` state in front of the draft.

Humans and authenticated agents edit the same current draft and create the same kind of reversible draft revisions.

---

## 2. Why change the current model

Today Albayan has three related representations of an unpublished manuscript:

```text
ArticleVersion(status=draft)
        │
        ▼
ArticleSession
        │
        ├── revision
        ├── last_saved_revision
        └── session/document.json
```

The browser updates the session and then performs a second explicit save from the session into the draft `ArticleVersion`. MCP exposes the same distinction through session read/edit tools plus `save_session`.

This creates concepts that are increasingly difficult to justify at the product boundary:

- session document vs saved draft document;
- session revision vs last saved revision;
- a formal-looking `ArticleVersion v1` before the article has ever been submitted;
- preview state stored on an `ArticleVersion` even when the preview is actually for a mutable session revision;
- metadata synchronization across `Article`, `ArticleSession`, and the draft version document;
- S3 overwrite ordering problems because `session/document.json` is mutable while its revision counter is stored in PostgreSQL.

The session layer originally provided a meaningful human-review boundary for agent work. That boundary is no longer the right abstraction now that humans and agents share the same editing surface and edits are already reversible through revision checks.

The irreversible boundary that matters is **submission/resubmission**, not “save session into draft”.

---

## 3. Domain invariants

### 3.1 Article

`Article` owns current authoring/workflow state.

It should gain explicit workflow state rather than deriving draft state from an unpublished `ArticleVersion`.

Conceptually:

```text
Article
  id
  submitted_by
  title
  abstract
  status
  current_draft_revision_id
  draft_revision_number
  created_at
  updated_at
```

The exact status enum may be refined during implementation, but it must be able to represent at least:

```text
draft
submitted / under_review
revision_requested
accepted
rejected
published
```

The important rule is that **article workflow state and formal version identity are not the same thing**.

Example: after reviewers comment on v1 and revisions are requested, `ArticleVersion v1` remains permanently the reviewed submission while `Article.status = revision_requested` and a new editable draft exists for the future v2.

### 3.2 ArticleDraftRevision

Add a new table/model approximately like:

```text
ArticleDraftRevision
  id                  UUID PK
  article_id          FK Article
  revision_number     integer
  storage_key         string
  document_hash       SHA-256
  created_at          timestamp
  created_by          nullable user id
  actor_type          human | agent | system
  reason              initial | autosave | ai_edit | metadata_edit | restore | migration
  mutation_id         nullable UUID / idempotency key
  restored_from_id    nullable FK ArticleDraftRevision
```

Required constraints:

- unique `(article_id, revision_number)`;
- each revision is immutable after creation;
- `storage_key` points to one immutable Document2 snapshot;
- a successful mutation never overwrites a previous revision object;
- identical no-op writes do not need to create another revision;
- MCP mutation/idempotency identifiers must continue preventing duplicate logical commands.

`Article.current_draft_revision_id` points to the current revision.

`Article.draft_revision_number` (or the current revision row’s `revision_number`) supplies the optimistic-concurrency token currently supplied by `ArticleSession.revision`.

### 3.3 ArticleVersion

`ArticleVersion` becomes exclusively a formal submitted manuscript round:

```text
ArticleVersion v1 = first submitted manuscript
ArticleVersion v2 = first resubmission after requested revisions
ArticleVersion v3 = later resubmission
```

There is **no `ArticleVersion v1` when a new article is merely created**.

Formal version content is immutable after creation. Reviews continue to point to `ArticleVersion`, which preserves the manuscript actually reviewed.

Operational/editorial records may evolve around a version, but the submitted document/assets/metadata snapshot must never be rewritten.

---

## 4. Storage layout

Use immutable object keys for draft snapshots.

Preferred conceptual layout:

```text
articles/{article_id}/
  draft/
    revisions/
      {draft_revision_id}/document.json
    assets/
      {asset_id}
    previews/
      {draft_revision_id}/compiled.pdf
      {draft_revision_id}/compile.log

  versions/
    v1/
      document.json
      assets/...
      compiled.pdf
    v2/
      document.json
      assets/...
      compiled.pdf
```

The revision UUID is the storage identity. PostgreSQL owns the friendly sequential `revision_number`.

Do not require S3 filenames to be allocated transactionally from the next sequential revision number.

### 4.1 Why immutable draft objects

A draft mutation should follow this failure-safe shape:

```text
1. read current revision N
2. produce canonical next Document2
3. write immutable S3 object for candidate revision
4. lock Article in PostgreSQL
5. confirm base_revision is still N
6. insert ArticleDraftRevision N+1
7. update Article.current_draft_revision_id
8. update Article metadata if required
9. commit
```

If the S3 write fails, PostgreSQL does not change.

If the database transaction fails, the worst expected result is an unreferenced/orphan S3 object. The application never points to it. Orphan cleanup can safely remove it later.

This is preferable to overwriting a shared `session/document.json` before the database revision commit.

---

## 5. Draft creation and first submission

### 5.1 New article

`create_article()` should stop creating `ArticleVersion v1` immediately.

New state:

```text
Article(status=draft)
└── DraftRevision 1
```

Revision 1 contains the canonical initial Document2 with the Article title/abstract and an empty body.

There is no formal version yet.

### 5.2 First submission

Assume the current draft is revision 64.

Submission must:

1. require human authentication;
2. lock/re-read the Article and current revision;
3. validate canonical metadata/document/assets;
4. require a fresh successful preview for the exact current draft revision if the current product rule remains;
5. create an immutable `ArticleVersion v1` package from DraftRevision 64;
6. copy referenced draft assets into the version package;
7. snapshot version-specific metadata;
8. update Article workflow state;
9. commit the formal version record.

The submitted package must be independent from draft-retention policy.

Do not make a permanent `ArticleVersion` depend on an object that may later be pruned from draft history.

---

## 6. Resubmission after review

Reviews remain attached to the formal version they concern.

Example:

```text
ArticleVersion v1
      │
      ├── Review A
      └── Review B

editor requests revisions
      │
      ▼
Article.status = revision_requested
      │
      ├── DraftRevision 65
      ├── DraftRevision 66
      └── DraftRevision 67

human resubmits
      │
      ▼
ArticleVersion v2
```

When revisions are requested, the editable draft should start from the last formal submitted content unless there is already a later valid current draft.

Creating that editable draft does not mutate v1.

Submitting v2 does not detach or rewrite reviews against v1.

---

## 7. Autosave and browser behavior

The browser should become autosave-first.

A typical flow:

```text
load revision 41
user types
short idle/debounce
PUT/PATCH draft with base_revision=41
backend creates revision 42
UI shows Saved ✓
```

Do not autosave every keystroke.

Use a short debounce and optionally a periodic save while continuous editing is active.

The exact interval is a product/UX choice and should not be hard-coded into the domain architecture.

### 7.1 Conflict behavior

Keep optimistic concurrency.

Every mutation supplies `base_revision`.

If the browser loaded 41 but an agent has already created 42:

```text
browser mutation based on 41
→ 409 revision_conflict
```

Do not use last-write-wins.

The client should reload/reconcile with the latest draft and make the conflict visible rather than silently overwriting agent or human changes.

### 7.2 No separate “Save session” boundary

A successful draft mutation is already persisted and reversible.

Therefore:

- remove `last_saved_revision`;
- remove “session has changes not yet saved into draft” state;
- remove `save_session` from MCP;
- remove the second browser persistence call that copies session state into the draft version.

The UI may still expose a user-friendly “Saved” indicator, retry state, and offline/error state.

---

## 8. Restore and history

Restoring history must create a new revision, not rewind or delete later history.

Example:

```text
57 normal edit
58 AI rewrite
59 normal edit
60 restore revision 32
```

Revision 60 contains the restored canonical document.

Set `restored_from_id` to revision 32 for provenance.

Do not delete revisions 33–59.

Restoring should restore the canonical draft document including title/abstract represented in Document2, and synchronize the authoritative current `Article.title` / `Article.abstract` accordingly.

Relational authorship (`ArticleAuthor`) must not be casually rewritten by document-history restoration.

---

## 9. Metadata ownership

Keep current host metadata rules, but simplify the synchronization topology.

Current authoritative editable metadata remains:

```text
Article.title
Article.abstract
ArticleAuthor relationships
```

Every created DraftRevision contains the same canonical title/abstract inside Document2 for portability/history.

A successful mutation that changes title/abstract must leave:

```text
Article.title == current DraftRevision Document2.meta.title
Article.abstract or "" == current DraftRevision Document2.meta.abstract
```

This removes the current three-way synchronization problem among Article rows, session JSON, and draft ArticleVersion storage.

`ArticleAuthor` remains relational authority for authorship. `Document2.meta.authors` must not become an alternate way to change author relationships.

### 9.1 Formal-version metadata

Historical screens must not read today’s mutable `Article.title` when rendering an old formal version.

At submission, preserve version-specific title/abstract either:

- in the immutable version Document2 snapshot; and/or
- in explicit `ArticleVersion.title_snapshot` / `abstract_snapshot` columns if query ergonomics justify them.

The implementation phase should choose one authoritative historical-read contract and test it.

### 9.2 Relationship to issue #86

Open issue #86 (“Make article title/abstract one synchronized metadata workflow across BuTeX and Article rows”) describes a real problem in the current session architecture.

This design does not close that issue automatically.

During implementation, reconcile #86 with this architecture: the target invariant remains valid, but synchronization becomes `Article ↔ current DraftRevision` rather than `Article ↔ ArticleSession ↔ draft ArticleVersion`.

---

## 10. Assets

Draft assets can no longer live under the current `ArticleVersion.storage_prefix`, because no formal version exists before submission.

Move editable article assets to an article-level draft namespace such as:

```text
articles/{article_id}/draft/assets/{asset_id}
```

DraftRevision JSON continues to reference asset IDs rather than embedding binary data.

On submission/resubmission:

1. inspect the exact submitted DraftRevision;
2. validate all referenced asset IDs;
3. copy the referenced assets into the immutable ArticleVersion package;
4. preserve content type and deterministic IDs/paths needed by export;
5. ensure a future draft asset replacement/deletion cannot alter the old formal version.

Do not duplicate every asset for every autosave revision. Draft revisions may share the article-level draft asset pool while formal versions receive immutable copies of the assets they reference.

Deletion guards must continue preventing removal of an asset referenced by the current draft.

---

## 11. Preview compilation

Preview compilation belongs to a **draft revision**, not to a session and not conceptually to an unpublished ArticleVersion.

Compile exactly DraftRevision N.

A successful preview record/result must identify at least:

```text
article_id
draft_revision_id
revision_number
document_hash
compile_id
status
compiled_at/error
```

Possible implementation shapes include a dedicated compile table or lightweight current compile fields referencing `ArticleDraftRevision`; choose the smallest model that keeps provenance explicit.

The key invariant is:

> A preview is fresh only for the exact immutable DraftRevision from which it was produced.

If revision 58 is compiled and revision 59 is later created, the revision-58 PDF remains historically valid for 58 but is stale relative to the current draft.

Do not create a new DraftRevision merely because the user clicked Preview.

Do not silently save an otherwise unsaved session before compile; in the new model the current draft revision is already persisted.

Formal submission may copy the fresh preview into the immutable version package or compile the formal package again, depending on the existing export contract. The final implementation must ensure the formal PDF and formal Document2 correspond to the same submitted content hash.

---

## 12. MCP contract

Rename the conceptual MCP surface from “session” to “draft”.

Target tools:

```text
get_draft_outline
get_draft_blocks
apply_draft_command
compile_draft
get_compile_status
get_article_pdf
```

`save_session` disappears.

`apply_draft_command` already persists by creating a new DraftRevision.

Keep the valuable current guarantees:

- typed BuTeX/Document2 commands;
- stable block/field/token identities;
- `base_revision` optimistic concurrency;
- `command_id` idempotency;
- actor provenance (`human` vs `agent`);
- asset validation;
- FastAPI as the business/security boundary;
- human-only submission/resubmission and editorial workflow transitions.

On `409 revision_conflict`, an agent must re-read the current draft before retrying.

The MCP server remains a thin protocol adapter and must not access PostgreSQL or S3 directly.

---

## 13. Retention

`ArticleVersion` is permanent according to journal retention policy.

`ArticleDraftRevision` is retention-limited.

Initial implementation should stay simple:

> Keep the latest 100 draft revisions per article.

Any revision needed for an in-flight migration/submission operation must not be pruned.

Because formal versions copy their own immutable document/assets, normal pruning never threatens submitted manuscript history.

Do not implement patch chains, CRDT/event-sourced history, or complex tiered retention in the first version.

A later policy may keep dense recent history and sparsify old autosaves, but it is outside the initial architecture migration.

---

## 14. Migration of existing data

Existing articles may currently contain:

- one `ArticleVersion(status=draft)`;
- an `ArticleSession` with a newer document than the saved draft version;
- submitted/reviewed ArticleVersions;
- session compile metadata on the current version;
- assets under version prefixes.

The migration must be explicit and deterministic.

### 14.1 Existing unpublished article

If an Article has only the current draft ArticleVersion:

1. choose the newest canonical editable content:
   - active session document if a valid current session exists;
   - otherwise current draft version document;
2. create DraftRevision 1 (or migrated revision N if preserving the old counter is useful);
3. move/copy current draft assets into the new draft asset namespace;
4. set Article workflow state to `draft`;
5. point `current_draft_revision_id` to the migrated revision;
6. do not retain the old unpublished ArticleVersion as formal v1.

### 14.2 Existing submitted/reviewed article

Preserve every already-formal ArticleVersion and all Review foreign keys.

If the article currently has an editable session/draft for future revision work, migrate that editable state into ArticleDraftRevision while keeping existing formal versions untouched.

If no editable draft exists because the article is frozen, do not invent one until workflow rules require revisions.

### 14.3 Compatibility window

During migration it is acceptable to temporarily support adapters that expose old `/session` API shapes internally backed by DraftRevision.

Do not keep the compatibility layer indefinitely.

The final state must remove `ArticleSession` and session-specific persistence semantics.

---

## 15. Three implementation phases

The migration must be delivered in exactly three implementation phases so each PR can remain reviewable and rollback-friendly.

### Phase 1 — Draft revision foundation and data migration

**Goal:** introduce the new durable model without immediately breaking browser/MCP consumers.

Implement:

- `ArticleDraftRevision` model/table and indexes/constraints;
- explicit Article workflow state and `current_draft_revision_id`;
- immutable draft snapshot storage helpers;
- article-level draft asset namespace;
- revision creation primitive with row locking, `base_revision`, hashes, provenance, no-op handling, and orphan-safe S3 ordering;
- migration/backfill for current unpublished drafts/sessions;
- migration rules preserving existing formal ArticleVersions and Review FKs;
- compatibility service adapters so existing `/session` endpoints can be backed by DraftRevision during rollout;
- tests for data migration, concurrency, S3/DB failure behavior, metadata invariants, existing submitted versions, and asset migration.

Phase 1 must **not** delete `ArticleSession` yet if live consumers still need compatibility.

Exit criteria:

- all new/updated editable state is representable as immutable DraftRevisions;
- existing articles are migrated without losing the newest editable content;
- existing formal versions/reviews remain unchanged;
- compatibility tests prove old consumers still function while backed by the new persistence primitive.

### Phase 2 — Unified browser/MCP editing and revision-bound preview

**Goal:** switch product behavior from explicit session saving to persisted/autosaved drafts.

Implement:

- first-class draft API routes/read models;
- browser debounce autosave with clear saved/error/conflict UI;
- remove the browser’s two-step “update session then save session to draft” behavior;
- draft history/restore backend primitive (UI can remain minimal if necessary);
- MCP rename/migration to draft tools;
- remove `save_session` from the target MCP contract;
- preserve command idempotency and actor provenance on DraftRevision;
- move preview compilation provenance from session/version revision fields to exact DraftRevision identity;
- return clean `409 revision_conflict` behavior to browser and MCP;
- update documentation and tests for simultaneous human/agent editing;
- compatibility aliases only where needed for a short rolling deployment window.

Exit criteria:

- browser and MCP both edit exactly one current draft state;
- every successful edit is already persisted as a DraftRevision;
- no user-visible `last_saved_revision` concept remains;
- preview freshness is determined by exact DraftRevision identity;
- an agent edit cannot be silently overwritten by a stale browser autosave, and vice versa.

### Phase 3 — Formal submission boundary and session removal

**Goal:** make `ArticleVersion` exclusively formal/immutable and delete the old architecture.

Implement:

- change `create_article()` so it creates Article + initial DraftRevision, not ArticleVersion v1;
- submission creates immutable ArticleVersion v1 from the exact current DraftRevision;
- resubmission creates v2/v3... while preserving reviews on earlier versions;
- copy formal document, referenced assets, metadata snapshot, and correct preview/PDF artifacts into the version package;
- update editor/reviewer/admin queries to use Article workflow state plus formal version history correctly;
- remove `ArticleSession` model/table after migration safety checks;
- remove `session/document.json`, `session/meta.json`, `last_saved_revision`, and session-specific compile fields;
- remove legacy `/document` draft-write bypass and obsolete `/session/save` semantics;
- remove compatibility aliases/routes/tools after all callers migrate;
- add simple latest-100 draft retention cleanup and orphan-object cleanup;
- update issue/docs references that still describe sessions as the target architecture.

Exit criteria:

- a never-submitted article has zero ArticleVersion rows;
- v1 is created only by first submission;
- v2+ are created only by formal resubmission;
- ArticleVersions are immutable, self-contained formal manuscript packages;
- Reviews always reference the exact formal version reviewed;
- no production code depends on `ArticleSession`, `last_saved_revision`, or mutable session JSON;
- browser, MCP, submission, compile, review, and migration test suites pass.

---

## 16. API direction

Final route names may be chosen during implementation, but the target semantics should look approximately like:

```text
GET  /api/v1/articles/{id}/draft
PUT  /api/v1/articles/{id}/draft
GET  /api/v1/articles/{id}/draft/outline
GET  /api/v1/articles/{id}/draft/blocks
POST /api/v1/articles/{id}/draft/commands
GET  /api/v1/articles/{id}/draft/revisions
POST /api/v1/articles/{id}/draft/revisions/{revision_id}/restore
POST /api/v1/articles/{id}/draft/compile
GET  /api/v1/articles/{id}/draft/compile/status
GET  /api/v1/articles/{id}/draft/pdf
POST /api/v1/articles/{id}/submit
```

The architecture does not require keeping both whole-document and command mutation routes forever. Both may call the same revision-creation primitive.

Human-only workflow routes must remain human-only even though agents may create reversible DraftRevisions.

---

## 17. Testing requirements

Each phase must add/adjust tests rather than deferring verification until cleanup.

At minimum cover:

- initial article creates DraftRevision but no formal ArticleVersion;
- full snapshot persistence and hash/no-op behavior;
- stale `base_revision` returns 409;
- concurrent human/agent updates cannot silently overwrite each other;
- repeated MCP `command_id` is idempotent;
- restore creates a new latest revision and preserves later history;
- metadata edits keep Article and current DraftRevision synchronized;
- authorship relationships are not changed by Document2 restore/meta operations;
- draft asset references validate correctly;
- submission copies only the correct referenced assets into a formal version package;
- old formal versions stay readable after draft assets/history are changed or pruned;
- compile result is bound to an exact DraftRevision and becomes stale after a newer revision;
- first submission creates v1;
- requested revisions followed by resubmission creates v2 without mutating v1;
- reviews remain attached to the correct ArticleVersion;
- migration prefers a newer valid session document over an older saved draft document;
- migration never converts an already submitted formal version into draft history;
- simulated S3 failure changes no DB pointer;
- simulated DB failure may leave an orphan object but never a live pointer to uncommitted state;
- legacy compatibility endpoints behave correctly during the temporary migration window;
- final Phase 3 tests prove session models/routes/storage semantics are absent.

---

## 18. Non-goals

Do not add these as part of this migration unless separately justified:

- CRDT collaborative editing;
- per-keystroke event sourcing;
- JSON diff/patch storage chains;
- permanent retention of every autosave;
- branching drafts;
- multiple simultaneous named drafts per article;
- direct MCP access to S3/PostgreSQL;
- agent authority to submit/resubmit or make editorial decisions;
- authorship changes inferred from Document2 metadata;
- a complex retention scheduler before simple fixed-count retention is proven insufficient.

---

## 19. Final architecture rule

After Phase 3 the system should be explainable in three concepts:

```text
Draft          = the current editable manuscript
Draft history  = immutable reversible autosave revisions
Versions       = immutable formal submission/review rounds
```

There is no separate editing “session”.

Humans and AI edit the same draft through the same revision/concurrency rules.

Saving is persistence; submission is the formal workflow boundary.

That is the architectural invariant future article-authoring work should preserve.
