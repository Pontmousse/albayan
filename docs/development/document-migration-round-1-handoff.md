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
