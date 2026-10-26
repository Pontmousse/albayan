# Round 3 Al-Bayan checkpoint — retiring first-generation BuTeX

Date: 2026-10-25. Companion BuTeX Round 3 branch `migration/document-round3-retire-legacy-20261025` stacks on Round 2 shared-math extraction; both target `develop` and remain unmerged.

## Dependency impact

Al-Bayan's maintained editor imports `@drghaliasri/butex/document2` and `@drghaliasri/butex/react-document2`; immutable revision preview uses `document2` and `react-document2-preview`. The backend worker client continues to call `/v1/document2/*`; normal MCP typed commands use active Document2 schemas. No Al-Bayan runtime code imports the retired first-generation `@drghaliasri/butex/document` or `@drghaliasri/butex/react-document` paths.

BuTeX Round 3 removes only the old React GUI, old `src/document/` document-specific model, old demo and obsolete exports. Shared mathematics was extracted first in Round 2. The current headless model, MathJax, worker and GUI remain present and named `Document2` until Rounds 4–6.

## Implemented verification

- Added `backend/tests/test_round3_butex_consumer_contract.py` asserting the actual editor/frozen-preview import paths, maintained worker URL set and continued presence of typed MCP schemas.
- Included this guard in the existing equation-integration CI workflow alongside the Round 2 immutable-revision regression.
- Preserved all current application behavior and existing frontend/package-lock, FastAPI schema, normal MCP interface, database, revisions and asset storage. No migration/alias/shim/deployment was introduced.

The old generation's package exports are intentionally retired **only on the unmerged BuTeX feature branch**, and are not ready for release until canonical unsuffixed replacements ship in later rounds. Cross-repository candidate tests and final frozen acceptance are still outstanding; do not merge, publish npm, deploy, or claim live verification of the branch.
