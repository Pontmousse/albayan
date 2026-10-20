# Equation authoring pipeline

[← Architecture index](README.md) · **Status: implemented**

Al-Bayan does not treat arbitrary LaTeX as a trusted browser MathObject. It uses a deliberate typed conversion pipeline:

```text
AI: supported canonical English/interoperability LaTeX
       |
       v
MCP: discover get_math_authoring_capabilities
     then apply_draft_command with typed math inline token
       |
       v
FastAPI: authenticate + validate command, article and base_revision
       |
       v
Burhan /convert: parse and convert supported canonical LaTeX
       |
       v
FastAPI: validate/project returned Arabic structured MathObject
       |
       v
BuTeX Document2 worker: apply inline-token command to Document2Json
       |
       v
Immutable ArticleDraftRevision document.json
       |
       v
BuTeX browser editor / MathJax render and edit Arabic mathematics
       |
       +-- optional inspection / reverse-conversion paths
```

## Boundary contracts

**AI/MCP.** First call `get_math_authoring_capabilities` to discover what the *current deployed pipeline* can safely round-trip. A supported inline math token uses a canonical `latex` value; do not send Arabic-specific BuTeX/Burhan macros or fabricate recursive MathObject JSON.

**FastAPI.** [`article_draft_service.apply_command`](../../backend/app/services/article_draft_service.py) intercepts canonical math tokens on `insert_inline_token` / `replace_inline_token`. It obtains article-scoped equation mappings and unit conventions, converts through [`burhan_client.py`](../../backend/app/services/burhan_client.py), validates the structured result, and passes the resulting strict token to the BuTeX worker. Concurrency and idempotency remain part of the surrounding draft command.

**Burhan.** The [Burhan repository](https://gitlab.com/drghaliasri/burhan3.0/-/tree/develop) owns parsing/conversion and its supported syntax. A general mathematical expression that ordinary LaTeX can represent is **not automatically guaranteed** to work through Burhan and BuTeX; use capability discovery and regression evidence rather than assumptions.

**BuTeX.** The [BuTeX repository](https://gitlab.com/drghaliasri/butex/-/tree/develop) owns the Document2 AST/worker, the structured equation editor and MathJax registration/rendering. Al-Bayan consumes its current `document2` / `react-document2` interfaces; the [naming cleanup is proposed](../proposals/butex-document2-naming.md), not applied.

## Reverse/diagnostic reads

Current Al-Bayan has [equation-specific routes](../../backend/app/routers/draft_equations.py) and [MCP equation tools](../../mcp_server/src/albayan_mcp/tools/equations.py) for retrieving/reconstructing equation information. Reverse conversion/English reconstruction must be distinguished from the authoritative stored Arabic MathObject; it is not another independently edited document tree.

The [Developer MCP](mcp.md) and separate browser testing can inspect individual stages, but a successful headless conversion is not proof that MathJax rendered correctly in the browser.

## Ownership and references

- [Math capability implementation](../../backend/app/services/math_authoring_capabilities.py)
- [Math capabilities endpoint](../../backend/app/routers/math_authoring.py)
- [Canonical equation integration notes](../equation-ai-architecture-reference.md) — additional design/verification context; verify current behavior against source
- [BuTeX worker client](../../backend/app/services/butex_worker_client.py)
- [Burhan client](../../backend/app/services/burhan_client.py)
