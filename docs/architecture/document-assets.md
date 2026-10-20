# Document2, validation and image assets

[← Architecture index](README.md) · **Current integration contract**

The **BuTeX library and worker** own the structure and semantics of `Document2Json`. Al-Bayan owns authenticated article storage, uploaded asset bytes, document revisions and compilation. These boundaries allow one editor to serve both a browser user and the normal authoring MCP.

## Document integration

- Browser: [article editor](../../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx) imports `Document2Json` from `@drghaliasri/butex/document2` and the versioned React editor from `@drghaliasri/butex/react-document2`. The [naming refactor](../proposals/butex-document2-naming.md) is not yet implemented.
- Backend: [BuTeX worker client](../../backend/app/services/butex_worker_client.py) calls private `/v1/document2/normalize`, `/outline`, `/commands`, `/references`, `/reference-index`, `/diff` and `/export` operations. These are **stateless** document operations.
- Authoritative persistence: [draft service](../../backend/app/services/article_draft_service.py) validates edits, normalized content and referenced assets before advancing the immutable revision head. The older `/session/commands` worker/API narrative is retired.

## Images: host-versus-editor ownership

| Concern | Owner |
| --- | --- |
| Upload, browse and delete article image bytes | Al-Bayan FastAPI / S3-compatible storage |
| Figure/image nodes, caption, label and editor interactions | BuTeX Document2 editor |
| Convert article inventory to editor asset choices | Al-Bayan frontend adapter |
| Resolve image URLs for the browser | Al-Bayan authenticated frontend API/resolver |
| Export asset keys referenced by a structured document | BuTeX worker + FastAPI validation |
| Embed referenced image bytes in compilation | FastAPI compiler/export flow |

Current host endpoints live under `/api/v1/articles/{id}/assets` for listing, uploading, deleting and retrieving article assets. Browser integration is in [`article-assets-panel.tsx`](../../frontend/src/components/dashboard/article-assets-panel.tsx), [`butex-image-assets.ts`](../../frontend/src/lib/butex-image-assets.ts), [`butex-images.ts`](../../frontend/src/lib/butex-images.ts) and [`articles.py`](../../backend/app/routers/articles.py).

The editor's image picker may select an asset already in the host inventory; selecting an image is distinct from **uploading** new bytes. The host does not bypass BuTeX figure structure to splice raw LaTeX into the stored document.

## Validation: incomplete draft versus valid export

An incomplete draft may be saved for later repair, but **a broken document should not compile or submit**. An empty image block must remain identifiable as an editor/document error rather than be silently dropped from the article. The frontend currently calls [`isButexDocumentValid`](../../frontend/src/lib/butex-validation.ts), including an empty-figure check, and the worker/export path validates the canonical document server-side. Do not assume the previously proposed BuTeX `isDocument2Valid` API has replaced the host compatibility helper without checking a published package/source version.

For changes to figures or validity semantics, test all three boundaries: BuTeX editor state, Al-Bayan saved revision, and PDF asset export; see [Playwright MCP tests](../development/playwright-mcp.md) and [equation/Document2 verification](../development/math-verification.md).

## Source of truth

- [Browser and host adapters](../../frontend/src/lib/)
- [Article assets router](../../backend/app/routers/articles.py)
- [Private BuTeX worker integration](../../backend/app/services/butex_worker_client.py)
- [BuTeX source](https://gitlab.com/drghaliasri/butex/-/tree/develop)
