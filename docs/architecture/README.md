# Al-Bayan architecture

**Status:** maintained implementation reference, originally reviewed against `develop` in October 2026. Recheck source for later changes. This directory explains **implemented code**, not a future design. Use source and exposed contracts to resolve differences when the code evolves.

## Architecture map

| Page | Read for |
| --- | --- |
| [System](system.md) | Runtime boundaries, ownership, and request flow |
| [Frontend](frontend.md) | Next.js structure, article editor, and API integration |
| [Backend](backend.md) | FastAPI routers, authentication, data and external services |
| [Database and storage](database.md) | Authoritative models and immutable document storage |
| [Document2 and images](document-assets.md) | BuTeX integration, figures/assets and document validity |
| [Other platform services](platform-services.md) | Notifications, issues, invitations, email and donations |
| [Article authoring](authoring.md) | Immutable draft revisions, commands, previews, submission and review |
| [Equation pipeline](equations.md) | Canonical LaTeX → Burhan → Document2 → BuTeX |
| [MCP surfaces](mcp.md) | User-facing authoring MCP versus developer-only diagnostics |

## Rules for reading this documentation

- **Current vs proposed:** All pages in this directory describe implemented `develop` behavior as reviewed, and source files remain authoritative. Plans must remain clearly labeled as plans.
- **Responsibility boundaries:** Al-Bayan authenticates, authorizes, orchestrates, stores and compiles. BuTeX owns structured document transformations/editor functionality. Burhan owns English→Arabic mathematical conversion.
- **Cross-repository contracts:** Prefer implementation and canonical interface descriptions in the owning repository over duplicated snapshots elsewhere.
- **No session architecture:** The old mutable `ArticleSession` / `/session/commands` workflow was replaced by immutable `ArticleDraftRevision` and `/draft/commands`.
- **Documentation organization:** [Development](../development/README.md) holds operational and diagnostic instructions. [Proposals](../proposals/README.md) contains the two maintained future designs. [Archive](../archive/README.md) preserves dated historical reports. Obsolete one-off audits, plans and duplicates were removed during the cleanup; Git history retains their content.

## Preserved proposals (not shipped)

- [BuTeX Document2 legacy naming cleanup](../proposals/butex-document2-naming.md): proposed renaming/removal of old editor surfaces; do not present as completed work.
- [Book authoring in Al-Bayan](../proposals/book-authoring.md) and [BuTeX book plan](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md): proposed book/unit model and editor, not present-day routes or models.

## Primary source entrypoints

- [Frontend page tree](../../frontend/src/app/) and [article editor route](../../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx)
- [FastAPI router composition](../../backend/app/main.py), [models](../../backend/app/models/), and [services](../../backend/app/services/)
- [Product MCP composition](../../mcp_server/src/albayan_mcp/server.py)
- [Developer MCP](../../dev_mcp_server/README.md)

This is an intentionally small navigation structure: add a page only for a distinct architectural boundary, not every feature ticket or past implementation phase.
