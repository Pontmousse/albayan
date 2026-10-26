# Al-Bayan — BuTeX 8.0.0 consumer release preparation

**Status:** draft. Pair this PR with [BuTeX MR !70](https://gitlab.com/drghaliasri/butex/-/merge_requests/70), targeting `develop`. **No deployment, npm publish, tag or production change is part of this PR.**

## Why 8.0.0

The Rounds 2–6 migration is merged into Al-Bayan and BuTeX `develop`. BuTeX replaces the public `document2` entrypoints, worker routes and CLI with canonical `document` equivalents and retires the first-generation editor; this is a breaking API change. The wire `DocumentObject`, `MathObject`, 29 command `op` values, source math LaTeX, assets, history and revisions remain stable.

## Review stages

1. While npm 8.0.0 is **unpublished**, pin the exact **8.0.0 pre-release CI tarball** using `frontend/butex-candidate.lock.json` (source SHA, pipeline, successful job, SHA-256), keep `frontend/package.json` using the current `file:.candidate/butex-candidate.tgz` source, and run authenticated GitHub Actions tests. Never synthesize an npm lockfile for an unavailable published package.
2. Cross-check against BuTeX MR !70's unpublished candidate artifact, including byte-for-byte hash, frozen 145-case acceptance specification hashes, full frontend tests, TypeScript and Next.js production build. The pinned tarball must match exactly.
3. **After** the reviewed BuTeX commit has been tagged `v8.0.0`, the GitLab publish job succeeds, and npm has actually made `@drghaliasri/butex@8.0.0` available, replace the temporary file dependency with the exact published npm version and its genuine generated `package-lock.json`. Remove the private-artifact-only preparation code and CI wiring in a separately reviewed follow-up or update this PR before merge. Verify npm provenance and rerun all integration tests.
4. Development-only coordinated deployment of BuTeX worker, Al-Bayan backend and frontend, with attested runtime commit/build version, comes **after** CI green. Then run the 145 immutable Round 7 E2E tests and stress/repetition checks.

## Known deployment blockers (observed 2026-10-26)

- BuTeX GitLab `develop` package CI succeeded, but Railway **development** service `albayan-butex` failed health checks because its start command is still `npm run serve:document2`. The migrated package only ships `npm run serve:document`. An authorized development service configuration change is needed; never alter production.
- Al-Bayan frontend Railway development build failed to install `file:.candidate/butex-candidate.tgz`, because the tarball is not in Railway's checkout/build context. The standard GitHub Actions pipeline successfully fetches and verifies it when the `GITLAB_BUTEX_READ_TOKEN` secret is present. Using the genuine released npm dependency resolves the artifact packaging dependency after release.
- Backend, MCP and Developer MCP development deployments succeeded at Al-Bayan merge head `4b3ad0ebad1eee198facd565409d442643866920`.
- The 145 frozen Round 7 end-to-end cases are not yet executed on the new development stack.

This document records release prerequisites, **not** evidence of a successful npm 8.0.0 publication or E2E certification.
