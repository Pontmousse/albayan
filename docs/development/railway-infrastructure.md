# Railway infrastructure — development and production

[← Development index](README.md) · [Browser testing](playwright-mcp.md)

**Observed from the connected Railway project `albayan` on 2026-10-19.** This is a factual infrastructure snapshot, **not** a desired future architecture, deployment prescription or guarantee of ongoing service health. The Railway project contains two persistent (non-ephemeral) environments: `development` and `production`.

## Environments and deployment branches

| | Development | Production |
| --- | --- | --- |
| Purpose | Feature integration, agent diagnostics and browser E2E tests | Public journal / real user traffic |
| Al-Bayan app source | `Pontmousse/albayan`, branch **`develop`** | `Pontmousse/albayan`, branch **`main`** |
| Frontend | <https://dev.albayan-journal.org> | <https://albayan-journal.org> |
| FastAPI | <https://api.dev.albayan-journal.org> | <https://api.albayan-journal.org> |
| User-facing MCP | <https://mcp.dev.albayan-journal.org/mcp> | <https://mcp.albayan-journal.org/mcp> |
| Developer MCP | `devmcp.dev.albayan-journal.org` | **Not deployed** |
| Playwright MCP | `playwright.dev.albayan-journal.org` | **Not deployed** |
| Railway region | `us-east4-eqdc4a` for listed services | `us-east4-eqdc4a` for listed services |

These are actual custom domains/source-branch settings observed in Railway, not inferred from filenames. Development code goes through PRs to `develop`; changes reach `main` only via an intentional release process. **A docs PR does not authorize a Railway deployment or production change.**

## Live service inventory (as observed)

| Service | Development | Production | Main role |
| --- | --- | --- | --- |
| `albayan-frontend` | Present | Present | Next.js Arabic/RTL browser application |
| `albayan-backend` | Present | Present | FastAPI orchestration, policy, workflow, SQL and S3 integration |
| `albayan-mcp` | Present | Present | Product-facing authoring MCP adapter over FastAPI |
| `albayan-dev-mcp` | Present | — | Restricted developer diagnostics and trace/suite analysis |
| `albayan-playwright-mcp` | Present | — | AI-operated headless Chromium browser tests |
| `albayan-butex` | Present | Present | Private stateless Document2 worker |
| `albayan-burhan` | Present | Present | Equation conversion |
| `albayan-xelatex-compiler` | Present | Present | PDF/LaTeX compiler |
| `albayan-postgres-db` | Present | Present | PostgreSQL persistence |

Railway reported **successful latest deployments** for all nine development services and all seven production services at review time. A successful deployment status is **not proof of functional correctness**. The Al-Bayan frontend/backend/product MCP (and development-only developer MCP) are explicitly connected to their respective monorepo branches. BuTeX and Burhan did not expose a repository source branch in the readback; verify their actual release/build provenance separately rather than assuming they follow the Al-Bayan Git branch.

### Component links and network exposure

```text
DEVELOPMENT                                    PRODUCTION
Browser/Next.js                                Browser/Next.js
dev.albayan-journal.org                       albayan-journal.org
       |                                               |
       v                                               v
FastAPI: api.dev...                           FastAPI: api.albayan-journal.org
       |                                               |
       +-- PostgreSQL / S3                             +-- PostgreSQL / S3
       +-- BuTeX / Burhan / XeLaTeX                     +-- BuTeX / Burhan / XeLaTeX
       ^                                               ^
       |                                               |
User MCP: mcp.dev.../mcp                       User MCP: mcp.albayan-journal.org/mcp
      (independent API client)                       (independent API client)

Developer MCP: devmcp.dev... --> bounded dev diagnostics only
Playwright MCP: playwright.dev... --> controls development browser only
```


The diagram summarizes logical service roles and permitted targets, not a network packet trace or a claim that those hosts are mutually isolated. **All three MCP surfaces are independent entry points**: user MCP for authoring, Developer MCP for bounded diagnostics, and Playwright MCP for browser control. Playwright controls a browser that visits the development frontend; Developer MCP inspects permitted development service boundaries.

### Database and object storage

Both environments provision a `postgres-volume` mounted at `/var/lib/postgresql/data` for their PostgreSQL service. Railway's inventory listed a **5000 MB** volume in development and a **500 MB** volume in production. An S3-compatible resource named `albayan-s3-bucket` is provisioned in each environment. The existence of similarly named resources **does not by itself prove that every external endpoint or credential is isolated**. Before a destructive test, independently verify the **development** connection targets and credentials without exposing their values.

The frontend/backend/product-MCP boundary is documented in [architecture/backend.md](../architecture/backend.md); the live Railway deployment information here is intentionally separate from timeless component responsibilities.

## Deployment/configuration observations

- Frontend, backend and product MCP use GitHub source `Pontmousse/albayan`: `develop` in development, `main` in production.
- Al-Bayan backend uses Alembic `alembic upgrade head` as a pre-deploy command in both environments.
- The BuTeX worker uses `npm run serve:document2` and has **no observed public service domain** in either environment.
- The compiler is configured from an image `elghaliasri/compiler-compiler:latest`; the database runs a PostgreSQL 18 Railway template image.
- Playwright MCP is a **development-only** service using `mcr.microsoft.com/playwright/mcp:latest`; [browser testing details](playwright-mcp.md).
- Backend start command currently includes `uvicorn ... --reload` in **both** environments, including production. This is an **observed configuration** worth reviewing separately; do not silently change it as part of a documentation PR.
- Railway exposes custom public hosts for the browser, API and user MCP, as well as development diagnostic/browser MCP. **Public host presence alone does not establish authentication or access restrictions.**
- Railway settings contain service-specific environment-variable *names* for Clerk auth, DB/S3, BuTeX/Burhan and compiler integration. This document intentionally records **no secret values or service tokens**.

## How an agent should investigate infrastructure safely

1. **Select the environment explicitly** in Railway's tooling (`development` by default for investigation). Read its service inventory and current deployments before drawing conclusions.
2. Determine which boundary is implicated: frontend, FastAPI, user MCP, Developer MCP, Playwright, BuTeX, Burhan, compiler, database or object storage.
3. Check the relevant service's deployment/configuration and bounded logs/health checks. Distinguish a successful deploy, an HTTP reachability check, and application correctness.
4. For actual browser behavior, use [Playwright MCP](playwright-mcp.md) against the development site and inspect the real network destinations. For equation conversion traces, use [Developer MCP](developer-mcp.md).
5. After a code fix, reproduce in development and verify the **normal MCP** if the end-user authoring path changed. A successful developer-only diagnostic is not sufficient.
6. **Never change or redeploy production** without a separate explicit request and verified target environment. No production browser tests, test-data mutations or secret disclosure.

When the observed Railway inventory changes, re-read it instead of treating this dated snapshot as live state. In particular, source settings and deployment status may change without an update to these Markdown pages.
