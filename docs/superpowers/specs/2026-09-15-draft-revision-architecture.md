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

## 2. Development reset: no backward compatibility or article-data migration

Albayan is still in development and there are no production articles that need preservation.

Current article/session/version data is disposable test data.

Therefore this architecture intentionally has **no backward-compatibility requirement for existing article data or old session APIs**.

Implementation should prefer deleting obsolete development state over building migration machinery for it.

Explicit rules:

- do not backfill existing `ArticleSession` rows into `ArticleDraftRevision`;
- do not convert existing draft `ArticleVersion` rows into draft revisions;
- do not preserve test reviews, assignments, article versions, compile state, or article assets merely to support development fixtures;
- do not build compatibility adapters that make old `/session` routes behave on top of the new draft model;
- do not keep old MCP session tool names as aliases after the cutover;
- do not maintain both old and new draft persistence models in production code;
- do not add migration-only fields, enums, provenance reasons, or branches to the new domain model;
- do not spend implementation effort preserving S3 objects created by test articles.

The cutover may use a destructive development migration/reset that clears article-domain test data and obsolete article S3 prefixes before or while introducing the new schema.

The cleanup must be scoped to article-domain development data. User/account data should not be deleted merely because article fixtures are disposable.

After the reset, all newly created articles use the new architecture from revision 1 onward.

This is a deliberate project decision, not a temporary omission. Future implementers should not reintroduce compatibility work unless real production data exists at that later time and a new requirement explicitly asks for it.

---

## 3. Why change the current model

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

The session layer originally provided a meaningful human-review boundary for agent work. That boundary is no longer the right abstraction now that humans and agents share the same editing surface and edits are reversible.

The irreversible boundary that matters is **submission/resubmission**, not “save session into draft”.

---

## 4. Domain invariants

### 4.1 Article

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

### 4.2 ArticleDraftRevision

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
  reason              initial | autosave | ai_edit | metadata_edit | restore
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

### 4.3 ArticleVersion

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

## 5. Storage layout

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

### 5.1 Why immutable draft objects

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

### 5.2 Development cleanup

Existing test article storage can be deleted rather than transformed.

The reset may remove obsolete article prefixes containing:

```text
session/document.json
session/meta.json
session/commands/*
versions/v*/document.json
versions/v*/assets/*
compiled.pdf
compile.log
```

Do not write copy/rename code whose only purpose is to preserve those development fixtures.

---

## 6. Draft creation and first submission

### 6.1 New article

`create_article()` must stop creating `ArticleVersion v1` immediately.

New state:

```text
Article(status=draft)
└── DraftRevision 1
```

Revision 1 contains the canonical initial Document2 with the Article title/abstract and an empty body.

There is no formal version yet.

### 6.2 First submission

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

## 7. Resubmission after review

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

## 8. Autosave and browser behavior

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

### 8.1 Conflict behavior

Keep optimistic concurrency.

Every mutation supplies `base_revision`.

If the browser loaded 41 but an agent has already created 42:

```text
browser mutation based on 41
→ 409 revision_conflict
```

Do not use last-write-wins.

The client should reload/reconcile with the latest draft and make the conflict visible rather than silently overwriting agent or human changes.

### 8.2 No separate “Save session” boundary

A successful draft mutation is already persisted and reversible.

Therefore:

- remove `last_saved_revision`;
- remove “session has changes not yet saved into draft” state;
- remove `save_session` from MCP;
- remove the second browser persistence call that copies session state into the draft version.

The UI may still expose a user-friendly “Saved” indicator, retry state, and offline/error state.

---

## 9. Restore and history

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

## 10. Metadata ownership

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

### 10.1 Formal-version metadata

Historical screens must not read today’s mutable `Article.title` when rendering an old formal version.

At submission, preserve version-specific title/abstract either:

- in the immutable version Document2 snapshot; and/or
- in explicit `ArticleVersion.title_snapshot` / `abstract_snapshot` columns if query ergonomics justify them.

The implementation phase should choose one authoritative historical-read contract and test it.

### 10.2 Relationship to issue #86

Open issue #86 (“Make article title/abstract one synchronized metadata workflow across BuTeX and Article rows”) describes a real problem in the current session architecture.

Its long-term invariant remains useful, but the implementation target changes to:

```text
Article ↔ current DraftRevision
```

not:

```text
Article ↔ ArticleSession ↔ draft ArticleVersion
```

Because development article data is disposable, #86 should not drive any session-data migration or compatibility work.

---

## 11. Assets

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

Existing development assets under old version prefixes may simply be deleted during the reset.

---

## 12. Preview compilation

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

Formal submission may copy the fresh preview into the immutable version package or compile the formal package again, depending on the export contract. The final implementation must ensure the formal PDF and formal Document2 correspond to the same submitted content hash.

Old session-bound compile metadata does not need to be transformed; it is development data and can be discarded.

---

## 13. MCP contract

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

Do not publish duplicate `session_*` aliases after the draft tools are introduced. Since this is a development cutover, clients should move directly to the new tool names.

---

## 14. Retention and cleanup

`ArticleVersion` is permanent according to journal retention policy once real submissions exist.

`ArticleDraftRevision` is retention-limited.

Initial implementation should stay simple:

> Keep the latest 100 draft revisions per article.

Because formal versions copy their own immutable document/assets, normal pruning never threatens submitted manuscript history.

Do not implement patch chains, CRDT/event-sourced history, or complex tiered retention in the first version.

A later policy may keep dense recent history and sparsify old autosaves, but it is outside the initial architecture.

### 14.1 Orphan-object cleanup

Immutable-object sequencing can leave an unreferenced candidate snapshot if S3 succeeds and a later DB transaction fails.

A simple cleanup job may remove draft revision objects that are not referenced by any `ArticleDraftRevision` after a conservative age threshold.

This is normal operational cleanup, not backward compatibility.

### 14.2 One-time development cleanup

At cutover, remove obsolete article-domain test state instead of migrating it.

Conceptually:

```text
clear disposable article/review/session/version fixture rows
remove obsolete article S3 prefixes
apply the new schema
start fresh with new test articles
```

Use normal FK/cascade-aware database operations or a deliberate development reset migration. Do not add production runtime code whose job is to recognize and translate old article shapes forever.

---

## 15. Three implementation phases

The work must be delivered in exactly three implementation phases.

The phases are a development implementation sequence, **not** a compatibility rollout. There is no requirement to preserve existing article fixtures between phases.

### Phase 1 — Core draft architecture cutover

**Goal:** replace the session/draft-version persistence model with DraftRevision as the only editable manuscript state.

Implement:

- destructive cleanup/reset of disposable article-domain development data and obsolete article S3 objects;
- `ArticleDraftRevision` model/table with immutable revision constraints;
- explicit Article workflow state and `current_draft_revision_id`;
- immutable draft snapshot storage helpers;
- article-level draft asset namespace;
- revision creation primitive with row locking, `base_revision`, document hashes, provenance, no-op handling, command idempotency, and orphan-safe S3 ordering;
- change `create_article()` to create `Article + DraftRevision 1`, with zero ArticleVersion rows;
- first submission creates immutable ArticleVersion v1 from the exact current DraftRevision;
- move draft preview compilation off unpublished ArticleVersion/session identity and bind it to DraftRevision;
- replace backend `/session` and legacy draft `/document` semantics with first-class `/draft` routes;
- remove `ArticleSession`, `last_saved_revision`, mutable `session/document.json`, `session/meta.json`, session command storage, and session-specific compile fields from the target runtime architecture;
- update the frontend API layer and MCP implementation enough to use the new draft routes directly rather than requiring compatibility aliases;
- update backend/MCP/frontend tests for the new baseline.

Do **not** implement:

- backfill of old article rows;
- preservation of old test reviews/versions;
- `/session` compatibility wrappers;
- old MCP tool aliases;
- data-copy logic for obsolete development assets.

Exit criteria:

- a new article has one DraftRevision and zero ArticleVersions;
- browser and MCP can read/mutate the same current draft through the new draft API;
- every successful draft mutation is persisted as an immutable DraftRevision;
- preview identity is revision-bound;
- first submission creates v1 and freezes its document/assets independently from draft state;
- no runtime persistence path depends on ArticleSession or mutable session JSON.

### Phase 2 — Autosave, history, restore, and conflict UX

**Goal:** make the new draft model pleasant and safe for continuous human + AI editing.

Implement:

- browser debounce autosave;
- periodic save while continuous typing if needed by UX testing;
- clear `Saving…`, `Saved`, error, and conflict states;
- clean `409 revision_conflict` handling in browser and MCP;
- draft revision history read API;
- restore operation that creates a new latest revision and records `restored_from_id`;
- minimal history UI sufficient to inspect and restore prior revisions;
- maintain `command_id` idempotency and human/agent provenance in history;
- ensure metadata changes create one canonical revision and keep Article title/abstract synchronized;
- remove any remaining manual two-step save assumptions from editor UI;
- ensure a newer AI edit cannot be silently overwritten by a stale browser autosave, and vice versa;
- add latest-100 revision pruning and orphan snapshot cleanup if operationally convenient here rather than Phase 3.

Exit criteria:

- ordinary browser editing autosaves without an explicit session-save boundary;
- current revision is always the persisted source of truth;
- stale writes fail visibly instead of overwriting newer work;
- restore never rewinds or deletes later history;
- user/agent provenance is visible enough for future history UX.

### Phase 3 — Formal version rounds, resubmission, and hardening

**Goal:** complete the journal workflow around the clean DraftRevision/Formal-Version split.

Implement:

- explicit `revision_requested` workflow transition;
- creation of a new editable draft from the last formal version when revision work begins;
- resubmission creates ArticleVersion v2/v3... without mutating prior versions;
- preserve Review foreign keys to the exact formal version reviewed;
- ensure formal document, referenced assets, metadata snapshot, and preview/PDF artifact are self-contained and immutable;
- update author/editor/reviewer/admin queries and screens to distinguish current Article workflow state from formal version history;
- historical metadata reads use the formal version snapshot rather than today’s editable Article metadata;
- finalize retention/orphan cleanup if not completed in Phase 2;
- remove stale documentation/comments/tests that still describe sessions as the target architecture;
- reconcile issue #86 acceptance criteria with the final `Article ↔ current DraftRevision` metadata invariant;
- run full browser/backend/MCP/workflow regression coverage.

Exit criteria:

- v1 exists only after first submission;
- v2+ exist only after formal resubmission;
- ArticleVersions are immutable, self-contained formal manuscript packages;
- Reviews always reference the exact formal version reviewed;
- a revision request creates/editable draft state without changing the reviewed version;
- current Article metadata and current DraftRevision metadata stay synchronized;
- no code/docs/tests treat ArticleSession or a draft ArticleVersion as part of the intended model.

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

Old `/session` routes are removed rather than supported as compatibility aliases.

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
- simulated S3 failure changes no DB pointer;
- simulated DB failure may leave an orphan object but never a live pointer to uncommitted state;
- test-data reset/cleanup leaves the new article schema in a clean usable state;
- old session routes/tools are absent rather than compatibility-shimmed;
- no tests require preservation or translation of pre-cutover article fixtures.

Do **not** add migration/backfill tests for old ArticleSession/article-version data. That behavior is explicitly out of scope.

---

## 18. Non-goals

Do not add these as part of this work unless separately justified:

- backward compatibility for pre-cutover article/session test data;
- migration/backfill of existing development articles;
- compatibility aliases for old session APIs or MCP tools;
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

There is no legacy-data compatibility layer for the development-era session model.

That is the architectural invariant future article-authoring work should preserve.