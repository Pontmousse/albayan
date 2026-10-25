# Round 6 completion and controlled merge-readiness — Al-Bayan

**Date:** 2026-10-25. **Review:** [PR #240](https://github.com/Pontmousse/albayan/pull/240), targeting `develop`, stacked on unmerged Round 2 PR #239; companion BuTeX [MR !69](https://gitlab.com/drghaliasri/butex/-/merge_requests/69) stacked on unmerged !68. No merge, release, npm publish, database migration, production change, or deployment was authorized for this round.

## Source contracts now canonical

- Strict typed host FastAPI and independent normal MCP schemas are `backend/app/schemas/document.py` and `mcp_server/src/albayan_mcp/schemas/document.py`, both exporting `DocumentCommand`, `DocumentMathObjectJson`, and `DocumentContractModel`; old schema entrypoint modules were deleted without aliases.
- The operation taxonomy moved to `backend/app/document_registry.py` and `DOCUMENT_COMMAND_GROUPS`; analytics and tests use it.
- Updated FastAPI/Burhan explanations, normal MCP tool descriptions (draft commands, asset, equation and article access), Developer MCP `document_command` stage and `document-roundtrip` suite. **Crucially, all 29 serialized command `op` string values are frozen**; `DocumentObject`, `MathObject`, nested math structure, source LaTeX, references, labels, asset ID and history metadata are byte-compatible.
- Round 4 worker backend clients target `/v1/document/*`. Round 5 frontend imports `document`, `react-document`, `react-document-preview`. Current code uses the existing authorized FastAPI draft endpoints and ownership scopes; no unsafe new endpoint or bypass.
- Added a strict `backend/tests/test_round6_document_contract.py` checking 29 typed `op` literals, public MCP vocabulary, Developer stage/suite names and absence of obsolete Python schema modules.
- Added independent `backend/tests/test_document_migration_spec_integrity.py` verifying fixed SHA-256 of **both frozen oracles**, v1 (66 IDs) and Addendum A (79 IDs), without mutating them. BuTeX's cross-repository CI independently compares both copies and their SHA-256.

## Reproducible unpublished candidate

`frontend/package.json` and `package-lock.json` install exactly `file:.candidate/butex-candidate.tgz` in this review branch, not published BuTeX 7.4.x. `frontend/butex-candidate.lock.json` pins source SHA, successful GitLab job/pipeline and tarball SHA-256. GitLab MR !69 builds this tarball and tests it directly against this PR's public HEAD with both frozen spec checks, targeted and full frontend tests, TypeScript and Next.js build. The workflow is independent of a public npm release.

**Known GitHub Actions setup blocker:** GitHub's own frontend step requires the private GitLab `GITLAB_BUTEX_READ_TOKEN` Actions secret (read_api scope). If missing, the step fails visibly rather than falling back to npm. Do not treat a blocked GitHub job as live candidate failure or as successful GitHub candidate attestation; the GitLab candidate integration gate must be green as well.

## Next approvals and Round 7

1. Review the true cumulative diff and merge prerequisite parent PR #239 and BuTeX MR !68 before PR #240 and MR !69, **only on owner's explicit approval**; re-run both CI gates for actual target merge heads. Do not accidentally merge into `main`.
2. The persistent development Railway BuTeX worker currently starts `npm run serve:document2` and previously reported obsolete `/v1/document2/*` and unverified build commit. Coordinated **development-only** deployment requires changing that start command to `npm run serve:document`, establishing a matching canonical worker/backend/frontend source provenance, and never touching production.
3. Round 7 separately executes the entire **145-case immutable acceptance matrix** and required stress counts, with independent **normal MCP** discovery/action, Developer MCP traces, development-site Playwright/MathJax editor evidence, compiler PDF, persistence/revision invariance and auth checks. Run against verified deployed candidate builds, not previously deployed code or only TypeScript unit tests. Do not edit frozen oracles to make tests pass.

The Round 6 source and CI gates are distinct from the future Round 7 E2E acceptance; do not claim Round 7 complete or merge readiness merely because a source test passed.
