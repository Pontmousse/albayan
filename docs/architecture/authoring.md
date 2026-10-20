# Article authoring and revision lifecycle

[← Architecture index](README.md) · **Status: implemented**

Al-Bayan has **one authoritative immutable draft-history model**. The earlier `ArticleSession` working-copy design and `/session/commands` endpoints are retired. Do not use older session-based documents as a present-day integration contract.

## Domain entities

- `Article`: article identity, ownership/status, current draft pointer and draft revision number.
- `ArticleDraftRevision`: immutable revision number, document key/hash, author/actor attribution, reason, asset references, math-unit conventions and revision-bound compile state.
- `DraftCommandReceipt`: idempotency record keyed by logical `command_id`.
- `ArticleVersion`: immutable **formal submission** snapshot, distinct from an editable draft revision.
- Author, editor, reviewer and review association models define the separate human publication workflow.

See [`app/models/article.py`](../../backend/app/models/article.py).

## Editing one draft

```text
browser loads current revision      agent gets outline / blocks
              |                               |
     PUT /articles/{id}/draft       POST /articles/{id}/draft/commands
              |                               |
              +--------- FastAPI -------------+
                            |
               check actor + ownership
                  + base_revision
                            |
                normalize / apply with
             private BuTeX Document2 worker
                            |
              immutable S3 document snapshot
                + SQL revision pointer / receipt
```

Important rules implemented in [`article_draft_service.py`](../../backend/app/services/article_draft_service.py):

1. A command supplies an existing `base_revision` and a unique `command_id`; callers must discover actual block/inline IDs rather than inventing them.
2. FastAPI validates edit permissions and optimistic revision matching. A stale base is a conflict, not an implicit merge.
3. Duplicate logical commands can return their recorded result; reusing one ID for a different request is rejected.
4. BuTeX normalizes resulting `Document2Json`; invalid data and missing referenced assets do not become new authoritative revisions.
5. Changed drafts become new immutable S3 objects and database revision rows. A canonical hash no-op can leave the head unchanged.
6. Restoring an older draft creates a **new** revision, not in-place mutation of the past; restore is human-authorized.

The browser's autosave path and the AI command path converge at this revision service. They are not two authoritative document stores.

## Preview, submission and review

- `POST /api/v1/articles/{id}/draft/compile` starts an explicit, revision-bound preview attempt.
- BuTeX exports canonical article LaTeX and asset references; FastAPI calls the configured compiler and stores the PDF/log against the exact revision and compile attempt.
- A formal submission requires a fresh successful preview for the current draft revision.
- `POST /api/v1/articles/{id}/submit` is human-only and records `ArticleVersion`, with the submitted `document.json`, referenced assets and compiled PDF copied into immutable formal-version storage.
- Editors/reviewers act on the formal article version through their separate authorized flows; draft writing by an agent is **not** submission or publication.

## Useful current API entrypoints

| Read/write | Endpoint |
| --- | --- |
| Load current draft | `GET /api/v1/articles/{id}/draft` |
| Browser autosave | `PUT /api/v1/articles/{id}/draft` |
| Agent-oriented outline / blocks | `GET /api/v1/articles/{id}/draft/outline`, `.../blocks` |
| Typed command | `POST /api/v1/articles/{id}/draft/commands` |
| Revision history / restore | `.../draft/revisions`, `.../restore` (human-only restore) |
| Preview | `POST .../draft/compile`, `GET .../draft/compile/status`, `GET .../draft/pdf` |

The route implementations are in [`app/routers/articles.py`](../../backend/app/routers/articles.py).

## Source and historical context

- [draft service](../../backend/app/services/article_draft_service.py)
- [article submission service](../../backend/app/services/article_service.py)
- [compiler service](../../backend/app/services/compile_service.py)
- [September 2026 session→revision design record](../superpowers/specs/2026-09-15-draft-revision-architecture.md) — historical decision context, **not** a separate active session API.
