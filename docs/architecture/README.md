# Al-Bayan architecture

**Status:** current implementation reference (reviewed against `Pontmousse/albayan` `develop` at `541b898a`, 2026-10-19). This directory explains **implemented code**, not a future design. Use source and exposed contracts to resolve differences when the code evolves.

## Architecture map

| Page | Read for |
| --- | --- |
| [System](system.md) | Runtime boundaries, ownership, and request flow |
| [Frontend](frontend.md) | Next.js structure, article editor, and API integration |
| [Backend](backend.md) | FastAPI routers, authentication, data, and external services |
| [Article authoring](authoring.md) | Immutable draft revisions, commands, previews, submission and review |
| [Equation pipeline](equations.md) | Canonical LaTeX → Burhan → Document2 → BuTeX |
| [MCP surfaces](mcp.md) | User-facing authoring MCP versus developer-only diagnostics |

## Rules for reading this documentation

- **Current vs proposed:** All pages in this directory describe observed `develop` behavior. Plans must remain clearly labeled as plans.
- **Responsibility boundaries:** Al-Bayan authenticates, authorizes, orchestrates, stores and compiles. BuTeX owns structured document transformations/editor functionality. Burhan owns English→Arabic mathematical conversion.
- **Cross-repository contracts:** Prefer implementation and canonical interface descriptions in the owning repository over duplicated snapshots elsewhere.
- **No session architecture:** The old mutable `ArticleSession` / `/session/commands` workflow was replaced by immutable `ArticleDraftRevision` and `/draft/commands`.
- **No code changes in this phase:** Existing in-depth specs, audits, and developer notes remain available while subsequent documentation cleanup is reviewed.

## Preserved proposals (not shipped)

- [BuTeX Document2 legacy naming cleanup](../butex-document-editor-legacy-removal-rename-audit.md): proposed renaming/removal of old editor surfaces; do not present as completed work.
- [Book authoring in Al-Bayan](../book-authoring-architecture.md) and [BuTeX book plan](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md): proposed book/unit model and editor, not present-day routes or models.

## Primary source entrypoints

- [Frontend page tree](../../frontend/src/app/) and [article editor route](../../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx)
- [FastAPI router composition](../../backend/app/main.py), [models](../../backend/app/models/), and [services](../../backend/app/services/)
- [Product MCP composition](../../mcp_server/src/albayan_mcp/server.py)
- [Developer MCP](../../dev_mcp_server/README.md)

This is an intentionally small navigation structure: add a page only for a distinct architectural boundary, not every feature ticket or past implementation phase.
