# Frontend architecture

[← Architecture index](README.md) · **Status: implemented**

The browser application under [`frontend/`](../../frontend/) uses Next.js App Router, React, TypeScript and an Arabic/RTL interface. Browser state is for interaction; FastAPI remains authoritative for articles, revisions, permissions and published versions.

## Layout and concerns

- [`src/app/`](../../frontend/src/app/): routes for public reading, account/settings, author workspaces and editorial/review workflows.
- [`src/components/`](../../frontend/src/components/): UI and reusable authoring panels.
- [`src/lib/`](../../frontend/src/lib/): HTTP clients, authentication integration, utilities and editor adapters.
- [`src/app/maktabi/maqalati/[id]/tahrir/page.tsx`](../../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx): current article editing screen.

## Article editor

The current editor imports **`Document2Json`** from `@drghaliasri/butex/document2` and dynamically mounts **`ButexDocumentEditor2`** from `@drghaliasri/butex/react-document2`. These are the *actual current names*, even though [a cleanup/rename is proposed](../butex-document-editor-legacy-removal-rename-audit.md).

The editing page coordinates:

1. Loading the article and latest authoritative draft revision via authenticated API calls.
2. A local BuTeX Document2 editor and document-validity checks.
3. Autosave through [`src/lib/draft-autosave.ts`](../../frontend/src/lib/draft-autosave.ts), with revision-aware conflict handling.
4. Supporting panels for images/assets, equation mappings, unit conventions, revision history and submission.
5. BuTeX/MathJax setup and preview rendering through browser-side integration helpers.

The browser does **not** directly call Burhan or persist structured equation ASTs to S3. The user-visible edit ultimately reaches FastAPI's draft API.

## Authentication and runtime

The frontend uses Clerk for signed-in user flows. Environment configuration belongs to `frontend/.env.local` (see `frontend/.env.example`); `NEXT_PUBLIC_API_URL` points browser API calls to FastAPI. Feature flags such as `NEXT_PUBLIC_MCP_ENABLED` and `NEXT_PUBLIC_DEV_MODE` control specific UI surfaces, **not** backend authorization.

From `frontend/`:

```bash
npm install
npm run dev
```

For backend/worker ownership and revision semantics, see [Backend](backend.md) and [Article authoring](authoring.md).

## Primary source

- [`frontend/package.json`](../../frontend/package.json)
- [article editor](../../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx)
- [autosave controller](../../frontend/src/lib/draft-autosave.ts)
- [MathJax loader](../../frontend/src/lib/butex-mathjax.ts)
