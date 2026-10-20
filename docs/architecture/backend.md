# Backend, security and persistence

[← Architecture index](README.md) · **Status: implemented**

[`backend/app/main.py`](../../backend/app/main.py) assembles FastAPI routers. The application uses SQLAlchemy with PostgreSQL, Clerk-backed human identity, explicitly scoped agent identity on approved routes, and an S3-compatible object store for draft snapshots/assets and PDFs.

## Code organization

| Path | What lives there |
| --- | --- |
| [`app/routers/`](../../backend/app/routers/) | HTTP endpoints for articles/drafts, math, references, reviews, editorial workflows, users, issues, notifications, donations, admin and diagnostics |
| [`app/services/`](../../backend/app/services/) | Business workflows, storage orchestration and upstream clients |
| [`app/models/`](../../backend/app/models/) | SQLAlchemy persistent entities, including article revisions and formal versions |
| [`app/schemas/`](../../backend/app/schemas/) | Typed request/response and Document2 contract validation |
| [`app/core/`](../../backend/app/core/) | Settings, authentication, actor rules, database, S3 and request tracing |
| [`alembic/`](../../backend/alembic/) | Database migrations |

## Identity and authorization

[`app/core/actor.py`](../../backend/app/core/actor.py) defines `ActorDep` for routes intentionally safe for both browser users and agents. It recognizes:

- Normal Clerk-backed human requests.
- Scoped `alb_...` agent keys (only while `MCP_ENABLED` is on).
- Supported Clerk OAuth JWTs through the MCP-facing agent path.

Agent requests require appropriate application scopes (for example `articles:draft:write`) **and** per-article ownership checks. They do not gain human-only authority by using the same endpoints. Submission, review/editorial decisions, restoring revisions and destructive operations retain explicit human-facing authorization boundaries.

The product MCP forwards credentials to FastAPI. The browser feature flags do not enforce server permissions; FastAPI does.

## Data ownership

- PostgreSQL models represent identities, article state, immutable draft-revision metadata, formal article versions, command receipts, review assignments and platform workflows.
- The S3-compatible store holds versioned `document.json` snapshots, assets and rendered PDFs/logs. The current article draft head points to an immutable stored document, not a mutable session.
- The BuTeX Document2 worker receives bounded documents and commands over private HTTP; it performs **stateless** normalization/outline/reference/index/diff/export/command operations.
- Burhan performs equation conversion; FastAPI validates the returned structured result before passing it into Document2.
- The compiler accepts XeLaTeX and necessary assets for the requested revision. It is not a public MCP operation.

For the up-to-date ownership map see [Database and storage](database.md); for other active services see [Platform services](platform-services.md). Figure and host/editor boundaries are covered in [Document2 and assets](document-assets.md).

## Operational notes

Set `DATABASE_URL`, Clerk settings and any required `S3_*`, `BUTEX_WORKER_*`, `BURHAN_*` and `COMPILER_URL` values using the relevant example environment files; never commit secrets. Local PostgreSQL is provisioned by [`backend/database/`](../../backend/database/) and migrations are applied using `alembic upgrade head`.

The application includes development-only routes **only when `DEV_MODE` is enabled**; [Developer MCP](mcp.md) is a separate service and must not be confused with unrestricted backend access.

## Source

- [FastAPI composition](../../backend/app/main.py)
- [config](../../backend/app/core/config.py)
- [actor boundaries](../../backend/app/core/actor.py)
- [article models](../../backend/app/models/article.py)
- [S3 helpers](../../backend/app/core/s3.py)
- [BuTeX worker client](../../backend/app/services/butex_worker_client.py)
