# Document migration — Round 4 Al-Bayan worker/client handoff

**Date:** 2026-10-25. **PR:** [#240](https://github.com/Pontmousse/albayan/pull/240) targeting `develop`; cumulative Round 3–4 branch stacked on unmerged PR #239. Companion cumulative BuTeX MR [!69](https://gitlab.com/drghaliasri/butex/-/merge_requests/69), stacked on unmerged MR !68.

## Implemented

- Updated **existing** private worker client `backend/app/services/butex_worker_client.py` for all canonical `/v1/document/*` routes: normalize, outline, references, reference-index, export, diff, apply commands and structured English MathObject projection. Existing HTTP `/v1/` version, JSON keys, command `op` values, request authentication, trace propagation, 5 MiB request limit, 15 s timeout, bounded errors and response validators remain unchanged.
- Updated `backend/app/services/butex_diagnostic_client.py` to `/v1/document/diagnostics/math-object`.
- Updated Python worker route/error/auth/diff/projection tests and subprocess integration worker output file to `document-cli.js`; continued exercising actual `mcp_server/tests/test_document2_schema.py` contract expectations without renaming the normal MCP public vocabulary (Round 6).
- Updated the Round 3 source-consumer guard to expect canonical private worker paths while still expecting `@drghaliasri/butex/document2` and `react-document2` **frontend imports**, which intentionally remain unchanged until Round 5.
- Extended the existing equation-integration workflow to execute worker diff/real-worker harness and MCP schema checks. No backend API schema, React package/lock, database, revision JSON, normal MCP tool or frontend runtime code changed during this round.

## Known cross-repo gate

BuTeX MR !69 promotes `src/document2/` to `src/document/` and `src/document2-cli/` to `src/document-cli/`, with `/v1/document/*` worker and `butex-document` CLI. Since all changes are unmerged, the deployed worker still exposes old `/v1/document2/*` routes; it is **not** currently a valid integration target for this PR's new routes.

Read-only development Railway inspection showed `albayan-butex` still configured to start `npm run serve:document2`; the candidate uses `npm run serve:document`. A coordinated, explicit development-only start-command change and provenance-attested worker deployment are prerequisites for live testing, and neither has been performed. No changes to production, npm publishing or database state are authorized.

The frozen 145-case matrix and browser/compiled-output acceptance remain for Round 7. Treat new contract CI as source/unit verification, not live candidate worker verification. Do not merge either branch without the maintainer's explicit approval.
