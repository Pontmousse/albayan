# Active proposals

These are deliberately **not implemented** in the current `develop` baseline. They remain design proposals, not claims of available features.

1. [**BuTeX Document2 naming / legacy editor cleanup**](butex-document2-naming.md) — retire the legacy React document editor, promote `ButexDocumentEditor2` to unversioned public naming where appropriate, then migrate Al-Bayan after publishing a compatible BuTeX release. The Document2 JSON/schema/worker version boundary is a **separate** decision; renaming the GUI should not silently rewrite it.
2. [**Arabic book/thesis authoring**](book-authoring.md) — chapter/unit documents, immutable book revisions, shared references, whole-book export and limited book MCP tools. See also [BuTeX's companion book plan](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md).

3. [**BuTeX legacy editor consumer migration execution plan**](butex-legacy-editor-consumer-migration-execution-plan.md) — **Status: PROPOSED EXECUTION PLAN — NOT IMPLEMENTED.** Source-driven, checkbox-tracked cross-repository phases for the frontend consumer, package/version transition, worker/MCP preservation and development acceptance gates. Its implementation inventory supersedes the historical naming audit. See the companion [BuTeX execution plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md).

Both original proposals and this execution plan must be rechecked against current source before implementation. Neither may be presented in the [current architecture pages](../architecture/README.md) as already shipped.

Other past design notes belong in [the historical archive](../archive/README.md) unless deliberately revived and reviewed as a new active proposal.
