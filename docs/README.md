# Al-Bayan documentation

Start with the [project README](../README.md). This repository keeps documentation in **exactly four top-level sections**, with an index in each.

| Section | Purpose |
| --- | --- |
| [`architecture/`](architecture/README.md) | **Current implemented system**: boundaries, data, article authoring, math, Document2/assets, platform features and MCP |
| [`development/`](development/README.md) | **How to operate, test and change it**: Railway, Playwright, Developer MCP, normal MCP, diagnostics, email and donations |
| [`proposals/`](proposals/README.md) | **Only two active proposals**: BuTeX Document2 editor naming cleanup and future book authoring |
| [`archive/`](archive/README.md) | Selected historical decisions, audits and investigation evidence; never an up-to-date API contract |

## Documentation policy

1. Current implementation claims belong in `architecture/`, grounded in source and live contracts.
2. Setup, deployment, debugging, runbooks and test procedures belong in `development/`.
3. Unshipped work is clearly labeled and belongs in `proposals/`. There are only **two** actively maintained proposals.
4. `archive/` retains only historical records with meaningful rationale. Old completed task plans and transient audits can be removed from the working tree because **Git history remains available**.
5. Keep operational READMEs near source when helpful, but link back to these four indexes instead of maintaining conflicting copies. Follow internal relative links and avoid duplicating entire cross-repository specifications.

**Safety:** documentation reorganization does not change application logic or deployed infrastructure. Never apply development tests or data writes to production by default.
