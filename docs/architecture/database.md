# Data model and storage ownership

[← Architecture index](README.md) · **Current implementation**

This is a maintained **model map**, not a frozen copy of every SQL column. For exact schema and constraints, follow the [SQLAlchemy models](../../backend/app/models/), [Alembic migrations](../../backend/alembic/) and live schema. Historical descriptions that placed article status solely on `article_versions` or used mutable `ArticleSession` are superseded.

## Authoring and review

| Model | Responsibility |
| --- | --- |
| `User` | Clerk-linked user identity and application profile |
| `Article` | Manuscript identity, workflow status, authoring head pointer and monotonically numbered draft revision |
| `ArticleDraftRevision` | One immutable structured-document snapshot with revision number, storage key/hash, actor provenance, referenced assets, math-unit conventions and preview state |
| `DraftCommandReceipt` | Idempotency receipt keyed by logical command UUID for typed edits |
| `ArticleVersion` | Formal submitted manuscript/version snapshot, separate from draft history |
| `ArticleAuthor`, `ArticleEditor`, `ArticleReviewer`, `Review` | Manuscript participants, assignments and peer-review reports |

The current `Article.status` controls the workflow; the draft head points to the current `ArticleDraftRevision`. An author's autosave or an agent's typed edit produces a new revision or a canonical no-op; it does not mutate previous snapshots. Formal submission creates an `ArticleVersion` and requires an up-to-date compiled PDF. Consult [Article authoring](authoring.md) for authorization, concurrency and submission behavior.

## Other data domains

[`backend/app/models/`](../../backend/app/models/) also contains invitation/account deletion records, agent tokens and MCP call logs, issues and votes, user notifications, email digests, donation email deduplication, and revision summaries. These are distinct product concerns, **not** versions of the authoring document.

- [`notification.py`](../../backend/app/models/notification.py): user-targeted notifications and read state.
- [`issue.py`](../../backend/app/models/issue.py): issues, votes and issue images.
- [`donation.py`](../../backend/app/models/donation.py): minimal duplicate-email prevention; Stripe remains the payment authority.
- [`agent_token.py`](../../backend/app/models/agent_token.py): hashed/revocable agent credentials with scope constraints.
- [`mcp_call_log.py`](../../backend/app/models/mcp_call_log.py): sanitized call audit information.

See [Platform services](platform-services.md) for related API boundaries.

## Storage domains

1. **PostgreSQL:** accounts, article/revision metadata, workflow/permissions, audit/deduplication and operational records. [`app/core/database.py`](../../backend/app/core/database.py) owns the session/engine.
2. **S3-compatible object storage:** immutable structured `document.json` blobs for draft revisions and submitted versions, document assets and revision-bound compiled PDFs/logs. [`app/core/s3.py`](../../backend/app/core/s3.py) provides the object operations.
3. **BuTeX worker:** stateless Document2 normalization, commands, export and reference extraction. It is not a second article database.
4. **Burhan:** equation conversion, not persistent per-article storage.
5. **Clerk and Stripe:** their corresponding identity/security and payment processor responsibilities; do not recreate their provider state unnecessarily in Al-Bayan.

## Changes and migration guidance

Update the SQLAlchemy model, schemas and Alembic migration together. Do not infer existing database columns from historical documents or mix `development` and `production` databases. For Railway service/volume inventory see [Development: infrastructure](../development/railway-infrastructure.md).

**Planned, not shipped:** `Book`/`BookUnitRevision` and associated book structures in [the book proposal](../proposals/book-authoring.md).
