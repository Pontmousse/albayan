# Round 5 — frontend candidate integration handoff

Date: 2026-10-25. Cumulative Al-Bayan draft PR #240 (`develop`) remains unmerged, stacked on unmerged Round 2 PR #239. Companion BuTeX cumulative draft MR !69 on GitLab is stacked on unmerged MR !68.

## Implemented

- Migrated the editor, image asset picker, autosave, article API types, history/frozen preview, validation, LaTeX export, MathJax initialization and editor CSS selectors to canonical `@drghaliasri/butex/document`, `@drghaliasri/butex/react-document`, `@drghaliasri/butex/react-document-preview`, `DocumentJson`, `DocumentNode`, `ButexDocumentEditor` and `injectBuTeXDocumentStyles`.
- Preserved callbacks, figure storage IDs, immutable draft/revision JSON, existing authenticated FastAPI endpoints, canonical `DocumentObject` and MathObject data, math directions and Arabic numeral mode; the normal MCP public schema/tool vocabulary is still scheduled for Round 6.
- Changed **frontend/package.json and frontend/package-lock.json in one commit** to `file:.candidate/butex-candidate.tgz`; the candidate is intentionally excluded from Git (no private tarball source committed). This replaces the old npm registry package for this unmerged development branch, never npm publication or downgrade.
- `frontend/butex-candidate.lock.json` pins the exact GitLab source SHA, successful CI pipeline/job and the SHA-256 printed by CI. `frontend/scripts/prepare-butex-candidate.mjs` fetches precisely that private artifact, verifies job provenance and checksum, and materializes the tarball before `npm ci`. The GitHub equation integration workflow calls this preparation before frontend tests, tsc and Next build.
- Added a frontend regression checking the lock, editor/preview separation, stylesheet scope and injection call. Existing Python backend/MCP and immutable revision tests remain unchanged except their frontend source-consumer guard.

## Required authorization / verification blocker

GitLab project `drghaliasri/butex` is **private**, so GitHub Actions requires the repository secret `GITLAB_BUTEX_READ_TOKEN` with read-API access to verify/download the artifact. This tool session **cannot inspect or configure GitHub Actions secrets**. If missing, the frontend step deliberately fails with an explicit BLOCKED message instead of falsely validating against old published BuTeX; this is a credential/setup blocker, not source-code proof of regression. A maintainer must provision it for full deterministic frontend CI. The local developer workflow is `GITLAB_BUTEX_READ_TOKEN=... node frontend/scripts/prepare-butex-candidate.mjs` followed by `cd frontend && npm ci && npm test && npx tsc --noEmit && npm run build`.

No development/production Railway settings or deployments, npm publications/tags, database migrations, merges or production changes performed. Full browser, compiled-output and frozen 145-case acceptance remain deferred until attested development deployment and Round 7.
