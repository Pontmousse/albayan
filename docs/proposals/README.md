# Active proposals

These are deliberately **not implemented** in the current `develop` baseline. They remain design proposals, not claims of available features.

1. [**BuTeX Document2 naming / legacy editor cleanup**](butex-document2-naming.md) — **historical GUI-only proposal, superseded for naming scope** by the full-stack execution plan below. The final target also canonicalizes the headless model, type names, CLI, worker routes and normal MCP while preserving persisted document JSON semantics.
2. [**Arabic book/thesis authoring**](book-authoring.md) — chapter/unit documents, immutable book revisions, shared references, whole-book export and limited book MCP tools. See also [BuTeX's companion book plan](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md).

3. [**BuTeX legacy editor consumer migration execution plan**](butex-legacy-editor-consumer-migration-execution-plan.md) — **Status: PROPOSED EXECUTION PLAN — NOT IMPLEMENTED.** Source-driven, **synchronized eight-round shared-gate** cross-repository plan covering frontend GUI/headless consumers, package/version transition, **backend worker URL and FastAPI route migration, MCP typed-command renaming**, preserved persisted JSON semantics and a **frozen shared acceptance/stress specification** and development acceptance gates. Its **full-stack naming decision** supersedes the historical GUI-only audit. See the companion [BuTeX execution plan](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/legacy-document-editor-migration-execution-plan.md).

Both original proposals and this execution plan must be rechecked against current source before implementation. Neither may be presented in the [current architecture pages](../architecture/README.md) as already shipped.

Other past design notes belong in [the historical archive](../archive/README.md) unless deliberately revived and reviewed as a new active proposal.

4. [**Frozen cross-repository Document acceptance and stress specification (v1)**](document-migration-frozen-acceptance-v1.md) — **Phase 0 proposed oracle; not yet frozen or executed.** Byte-identical copy in BuTeX. Owner review/hash freeze before implementation, no in-place edits during Rounds 1–6, full Developer MCP-centered stress verification in Round 7, with separate normal MCP/browser evidence where required. [BuTeX mirror](https://gitlab.com/drghaliasri/butex/-/blob/docs/legacy-editor-execution-plan-2026-10-20/docs/proposals/document-migration-frozen-acceptance-v1.md).
