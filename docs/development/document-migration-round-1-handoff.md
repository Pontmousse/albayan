# Document migration — paired Round 1 handoff

> **Status: IN PROGRESS — do not check Round 1 complete in either plan.** Round 0 is approved/frozen. The linked implementation branches remain UNMERGED. This is an editable round ledger and NOT the immutable acceptance oracle.

## Paired implementation requests

- Al-Bayan: [GitHub PR #238](https://github.com/Pontmousse/albayan/pull/238), branch `migration/document-canonical-rounds-1-7-20261021` targeting `develop`.
- BuTeX: [GitLab MR !67](https://gitlab.com/drghaliasri/butex/-/merge_requests/67), same branch name targeting `develop`.
- Change boundary: strictly mechanical naming/removal only after diagnostics. **No end-user behavior, UI/UX, database, stored JSON, math, compiler, security, autosave, or workflow changes. No source-comment cleanup, unrelated refactoring or aliases.**

## Freeze integrity and test result keys

- Immutable v1: **66** cases; SHA-256 `6457a3d1abe43ba4cde16bd9b287d097978671db5ba3657c28099b1c6e26ca8e`.
- Immutable Addendum A: **79** cases; SHA-256 `dd96dae156fd2d026ca75ca390bb8c63104bdb938ecea7b6b0359dfbe905591e`.
- Both original documents remain byte-identical in Al-Bayan and BuTeX, unchanged.
- **145 distinct cases** are identified by `v1:LOCAL_ID` or `addendumA:LOCAL_ID`. Six mathematical short IDs (`MTH-01`–`MTH-06`) overlap and must not overwrite each other in any result database or report.
- See [editable coverage manifest](document-migration-coverage-manifest.json): it enumerates every case and initial candidate source tests/observation planes; **all cases are `not_run` and source mapping remains to be verified**. Offline CI guards enforce both SHA-256 fingerprints and namespaced case completeness.

## Implemented in Round 1 so far

**BuTeX (MR !67):** adds a bearer-token-protected stateless `diagnose_contract` worker action at `POST /v1/document2/diagnostics/contract`, using the *same route constants* that real HTTP dispatch uses; returns operation paths and advisory runtime build metadata. Existing Document2 headless/React/binary/routes remain unchanged. Adds protocol/auth/stdin tests and a real synthetic worker output capture via `test/document_migration_baseline.test.ts`. GitLab MR `package_test` publishes the reproducible output as `artifacts/document-migration-baseline.json` (CI job artifact), including source `CI_COMMIT_SHA`, package version and all synthetic requests/responses. No persistent article data touched.

**Al-Bayan (PR #238):** new `backend/app/services/document_diagnostic_service.py` and fixed `POST /api/v1/dev/diagnostics/document` behind normal actor authentication plus `DEV_MODE`, with 128 KiB payload guard, safe status/error classification and delegation to **existing** private BuTeX client functions. Adds `dev_document_contract_snapshot`, `dev_document_inspect`, `dev_document_compare` to the **Developer MCP only**, plus fixed-url bounded HTTP client, typed allowlisted operations, exact structural JSON comparison, trace correlations and precise secret redaction that does **not** hide document `tokens` or `token_id`. Extends named regression suite discovery/runner with 14 starter synthetic cases (one `document-final-stress` placeholder explicitly blocked until Round 7), offline tests and CI wiring. Does not alter normal user MCP, frontend, article state or legacy worker routes.

## Observed verification and open blockers

- The original planning PR #236 and MR !66 were merged to `develop` before these implementation branches were created.
- Al-Bayan Developer MCP and existing equation integration CI previously passed on the implementation branch; latest CI results must be checked against the **latest** head SHA before closing this round.
- BuTeX package build/typecheck/Vitest and MR base guard previously passed on the implementation branch; verify the new pipeline after later route-table and coverage-manifest commits. Earlier successful job [#17354340920](https://gitlab.com/drghaliasri/butex/-/jobs/17354340920) produced a ZIP artifact with the synthetic baseline. This proves tested worker code at that earlier commit, **not deployment compatibility**.
- **Live Dev MCP access is blocked in this agent connection:** a `dev_capabilities` invocation returned `UNAVAILABLE: McpServerError: Connection failed`. Railway shows the persistent *development* Developer MCP service deployed, but that does not prove callable diagnostic access.
- Railway `development` backend/Developer MCP still pointed at prior `develop` deployment when observed (backend commit `32e67aba2195ac5940953d1a60b1f64aee31c0bc`, before this migration). Unmerged PR sources were not live. Independently deployed BuTeX worker's revision is **not attested** by Railway deployment metadata. Do not claim the new diagnostics ran live or that a verified old-worker response baseline was captured through Developer MCP.
- The authenticated new diagnostic route and actual live worker build **must be tested in an authorized, explicitly identified development-only candidate environment** before the shared Round-1 gate can be checked. No deployment was made during this round.

## Next safe steps before checking Round 1 complete

1. Inspect the latest CI runs for PR #238 and MR !67; correct test-only defects, preserve original behavior.
2. Read/download the latest BuTeX baseline artifact; attest exact source commit/package version and compare it with independently deployed worker build identity.
3. Restore the Developer MCP connector or use an explicitly approved isolated development feature deployment; invoke `dev_capabilities`, `dev_document_contract_snapshot` and bounded document regression suites against an attested real worker/backend pair, collecting trace IDs and stage evidence.
4. Confirm that the 145-case coverage manifest covers each retained source test/action; map any missing cases during the Round-2 source audit, not by rewriting frozen documents.
5. Record both final implementation-branch head SHAs, actual CI URLs, worker/backend identity, diagnostic results and missing observations in the two accumulating PR/MR descriptions. Check Round 1 in **both plans simultaneously** only after its shared harness + real pre-rename baseline gate passes.

**Never run the complete frozen 145-case acceptance and repeated stress loops before Round 7.** Focused diagnostic suites and offline unit tests during Round 1 are permitted and do not imply final acceptance.

## Development-only version and deployment sequence (2026-10-22)

The accumulating Round-1 branches now carry **BuTeX package version 7.4.3** (including its package-lock root metadata) and **Al-Bayan Developer MCP project version 0.1.1**. Neither version number changes any existing document semantics or GUI exports. This is a diagnostic-only patch release; the later incompatible Document2→Document package API renaming must receive a separate breaking/major version at its approved final release.

**Safe sequence:** merge the diagnostic MR into BuTeX `develop`; let its `develop` CI pass; only then create tag `v7.4.3` **on the verified BuTeX develop commit** when npm publication is authorized. GitLab `publish_npm` automatically publishes to the public registry for matching `vX.Y.Z` tags. A version bump in the MR is not itself a publish or a deployment. Verify npm registry availability before any dependent install. Merge Al-Bayan PR into `develop` after confirming its tests and deployment compatibility. Redeploy **development** backend and **development** Developer MCP, and restart/reconnect the ChatGPT Developer MCP connector so the new tools are discovered. Explicitly deploy or verify the development BuTeX worker from the pinned `v7.4.3` source revision; npm publication does **not** automatically update a Railway worker deployment.

**Frontend protection:** `frontend/package.json` and `frontend/package-lock.json` intentionally remain at `^7.4.2` and resolved `7.4.2` in Round 1, because the new diagnostic endpoints and Developer MCP tools do not require new frontend package exports. The main branch remains unmodified, but its `^7.4.2` range can resolve a newer 7.x if its lockfile is regenerated or installs ignore the lock. Use `npm ci` and do not update production lockfiles; verify all production deployments are built from main's pinned lockfile. Do not assume main is immune to an npm patch publication merely because its package.json is unchanged.

**Validation after reconnect:** `dev_capabilities` must advertise the new document tools/suites; `dev_health` must show backend, Burhan and worker reachable; `dev_document_contract_snapshot` must report the live route map and build metadata; `dev_document_inspect` must execute authenticated stateless synthetic fixtures against the real development worker; run focused named document suites, capture trace IDs and attach reports. Match the live worker's source revision and version against the tag/CI artifact, and explicitly record any unverified provenance. Connection and discovery alone are not sufficient for Round-1 completion.

**Approval boundary:** no tags, npm publication, merges, Railway deployments or production changes are performed by the current branch updates. The user will choose when to merge/tag/reconnect. The complete frozen 145-case acceptance and stress test remains deferred to Round 7.

## Development worker deployment decision (2026-10-22)

The owner confirmed that **no npm tag, package version bump, or new Railway service is required** for Round-1 worker diagnostics. The temporary `7.4.4` bump was reverted; BuTeX remains `7.4.3`. The existing Railway `development` service `albayan-butex` already executes `npm run build` followed by `npm run serve:document2`. The new authenticated `POST /v1/document2/diagnostics/contract` is part of that existing worker and must be deployed there, not to a second worker service.

**Important deployment caveat:** Railway's `albayan-butex` service has no linked Git source or container image in its live configuration, so merging GitLab MR !67 does **not** itself deploy it. An explicit, development-only source build/deployment from the merged BuTeX `develop` commit is still necessary. Capture that exact commit identity as baseline provenance. Al-Bayan frontend stays pinned to its existing BuTeX `7.4.2` lockfile; no dependency update is required for backend/worker diagnostics. Al-Bayan backend and Developer MCP can redeploy from the merged GitHub `develop` commit.

**Do not create a new Railway service or publish an npm tag.** Production `main` and production Railway services remain untouched.
