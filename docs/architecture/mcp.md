# MCP: authoring versus development diagnostics

[← Architecture index](README.md) · **Status: implemented**

The repository has **two intentionally separate MCP servers**. Conflating them is a security and correctness mistake.

## User-facing MCP (`mcp_server/`)

[`mcp_server/src/albayan_mcp/server.py`](../../mcp_server/src/albayan_mcp/server.py) composes typed tools from small families under `tools/`: profile, articles, drafts, equations, units and assets.

- Remote clients use Streamable HTTP with supported OAuth, or scoped personal `alb_...` credentials where applicable; local stdio is a development option.
- Tools call FastAPI through [`api_client.py`](../../mcp_server/src/albayan_mcp/api_client.py), forwarding the user's credential. They do **not** import SQLAlchemy models, access S3, call Burhan or command the BuTeX worker directly.
- Examples: `get_draft_outline`, `get_draft_blocks`, `apply_draft_command`, `get_math_authoring_capabilities`, `compile_draft`.
- `apply_draft_command` works with one typed Document2 operation, known IDs, `base_revision` and `command_id`.
- FastAPI enforces identity, author ownership, agent scopes and non-agent-safe workflow boundaries. No MCP tool may bypass submission/review/administrative checks.

Normal content-creation agents should use this MCP, not the development diagnostics surface.

## Developer MCP (`dev_mcp_server/`)

[`dev_mcp_server/README.md`](../../dev_mcp_server/README.md) describes a separate service for trusted investigation **against development services**. It can check configured reachability, inspect trace stages and exercise bounded equation/regression diagnostics without becoming a general-purpose administrative or shell interface.

Its remote access has separate Clerk OAuth/developer authorization. Its generic HTTP access is constrained to configured development origins and read methods; specialized diagnostic operations are limited and reviewed. It must not be described as production authoring capability, a general DB console, or proof of browser rendering.

For equation failures, reason across:

```text
canonical LaTeX -> MCP contract -> FastAPI -> Burhan AST
-> Document2 worker -> stored JSON -> BuTeX editor -> browser/MathJax
```

A trace or headless test establishes only the stages it actually observed. Browser/UI rendering requires separate browser evidence (for example development-site Playwright checks).

## Authentication is enforced at FastAPI

[`backend/app/core/actor.py`](../../backend/app/core/actor.py) exposes `ActorDep` on explicitly agent-safe endpoints and `require_actor_scope` for application-level scopes. Human-only routes retain human Clerk dependencies. UI feature flags and MCP tool availability are not security substitutes.

## Current docs / code

- [Product MCP source](../../mcp_server/src/albayan_mcp/)
- [Developer MCP source](../../dev_mcp_server/src/albayan_dev_mcp/)
- [FastAPI actor model](../../backend/app/core/actor.py)
- [Developer investigation guidance](../dev-mcp-investigation-workflows.md)
- [Product MCP detailed guide](../../mcp_server/Documentation.md) — supplementary operational notes; treat historical session terminology as superseded.
