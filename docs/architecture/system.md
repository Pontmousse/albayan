# System and component boundaries

[← Architecture index](README.md) · **Status: implemented**

Al-Bayan is a monorepo for an Arabic scientific journal platform. The browser and AI authoring clients share the **FastAPI business boundary**: neither writes directly to the database or document store.

```text
Arabic/RTL browser (Next.js)          AI client
   |                                    |
   | authenticated API                  | MCP tools (HTTP / local stdio)
   |                                    v
   |                           User-facing MCP adapter
   |                                    |
   +------------------------------------+
                     |
                     v
              Al-Bayan FastAPI
       auth, policy, article workflow,
       immutable revisions, persistence
         |            |           |
         v            v           v
    PostgreSQL    S3-compatible   private BuTeX
    models/IDs    objects         Document2 worker
                                    normalize/commands/
                                    outline/export
                       |
                       +-- Burhan equation service
                       |      English LaTeX → Arabic math AST
                       +-- XeLaTeX compiler service
                              revision-bound PDF
```

The diagram shows logical dependencies, not guaranteed deployment topology or service readiness in every environment. For the **observed Railway deployment**, separate production/development boundaries and actual service domains, see [Development: Railway infrastructure](../development/railway-infrastructure.md).

## Repository responsibilities

| Location | Responsibility | Boundary |
| --- | --- | --- |
| [`frontend/`](../../frontend/) | Next.js App Router, RTL UI, browser authoring and review surfaces | Uses authenticated HTTP; does not own database records |
| [`backend/`](../../backend/) | FastAPI routes, permissions, state transitions, SQLAlchemy and storage | Only authoritative business/persistence tier |
| [`mcp_server/`](../../mcp_server/) | User-facing typed tools over backend HTTP | Thin adapter; no direct DB/S3/worker access |
| [`dev_mcp_server/`](../../dev_mcp_server/) | Restricted development-only diagnostics | Separate authenticated development surface, not an authoring API |
| [BuTeX](https://gitlab.com/drghaliasri/butex/-/tree/develop) | Document2 AST/commands/worker; browser editor and MathJax rendering | Stateless document operations; no article/user ownership |
| [Burhan](https://gitlab.com/drghaliasri/burhan3.0/-/tree/develop) | Parse/convert canonical equations into Arabic mathematical structure | No article persistence or document authorization |
| Compiler service | XeLaTeX rendering for one exact draft/export | Invoked through FastAPI; not directly by MCP |

## Main flows

1. **Human authoring:** browser → FastAPI article/draft endpoints → normalized `Document2Json` → immutable revision.
2. **Agent authoring:** MCP typed tool → FastAPI scope/ownership check → Document2 command (and Burhan for canonical math tokens) → immutable revision.
3. **Preview:** FastAPI exports one saved revision through BuTeX, provides assets to a configured compiler, and stores PDF/log tied to that revision.
4. **Formal submission:** human-authorized transition freezes a version derived from the validated current revision. Editorial/review decisions operate on formal versions, not mutable authoring sessions.

## What's not yet implemented

The book/unit architecture documented in [book authoring proposal](../proposals/book-authoring.md) is a **proposal**. There are no shipped book-specific persistence models, authoring routes, or MCP tools in this reviewed tree. The separate BuTeX naming-cleanup document is likewise a proposal, not a declaration that all legacy entrypoints are removed.

For precise ownership see [Database and storage](database.md), [Document2/assets](document-assets.md) and [Platform services](platform-services.md).

## Source map

- [`backend/app/main.py`](../../backend/app/main.py): mounted routers and diagnostic feature gate
- [`backend/app/core/config.py`](../../backend/app/core/config.py): service URLs and feature flags
- [`backend/app/services/article_draft_service.py`](../../backend/app/services/article_draft_service.py): canonical revision lifecycle
- [`backend/app/services/butex_worker_client.py`](../../backend/app/services/butex_worker_client.py): worker integration
- [`backend/app/services/burhan_client.py`](../../backend/app/services/burhan_client.py): equation service client
- [`backend/app/services/compile_service.py`](../../backend/app/services/compile_service.py): compiler integration
