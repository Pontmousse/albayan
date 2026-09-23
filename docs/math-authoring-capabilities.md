# AI math authoring capability contract

Albayan exposes `get_math_authoring_capabilities` so an AI can discover the canonical LaTeX it may generate before it sends an `insert_inline_token` or `replace_inline_token` math command.

The write path remains unchanged:

```text
AI canonical LaTeX
  -> MCP apply_draft_command
  -> FastAPI math-token expansion
  -> Burhan parse / Arabic conversion
  -> strict Document2 MathObject token
  -> BuTeX Document2 worker
  -> immutable structured draft
```

The capability tool is a pure read. It never reads or mutates an article. New math should use only the response's `round_trip_safe` section and ordinary canonical English LaTeX. Burhan/BuTeX Arabic-side or output-only macros such as `\ad`, `\arsum`, `\arprod`, `\arlim`, `\boldarabic`, `\arsqrt`, `\butextakween`, `\unit`, and `\idx` are not AI authoring syntax.

## Why this is a snapshot

Burhan's low-level command parser deliberately preserves an unknown alphabetic command such as `\foo`. Therefore "the parser returned an AST" is broader than a useful supported-authoring contract. In addition, some Burhan structures can be stored but cannot currently be imported back into the BuTeX equation editor without loss.

The Albayan contract is therefore a conservative snapshot of the intersection of:

- Burhan canonical-English parser/converter support;
- Albayan's strict `DocumentMathObjectJson` bridge; and
- BuTeX editor re-import support.

The response distinguishes `round_trip_safe` from `accepted_but_not_round_trip_safe` rather than pretending all parser-pass-through syntax is supported.

## Reviewed source revisions

The snapshot in `backend/app/services/math_authoring_capabilities.py` is pinned to:

- Burhan `drghaliasri/burhan3.0` commit `7ad84b2bdfd4c7eb95c2ad7c584b8e2a93207159`;
- BuTeX `drghaliasri/butex` commit `7f55227b4cf368efb26b937c1729ba2e89eee865`.

The source file list is returned in the capability response itself. The key Burhan definitions are `latex_parser.py` (`parse_command`, `parse_atom`, `parse_delimiter`, `parse_math_environment`, `fill_chain`), `commands.py` (canonical command mappings), `nodes.py` (`CommandObject`, `EnvObject`, `MathObject` and math modes), `base_node.py` (`reverse_delimiter`), and `equation_processor.py` (the `/convert` normalization/build path).

The important BuTeX round-trip boundary is `src/document/mathEditorAdapter.ts`, backed by the atomic command/operator/accent registries and the Document2 worker.

## Updating the contract

When Burhan or BuTeX math support changes:

1. review the pinned source files rather than documentation alone;
2. update the whitelist conservatively and bump the pinned commit(s);
3. ensure every advertised command and environment still has a case in `burhan_verification_cases()`;
4. run `backend/tests/test_math_authoring_capabilities.py` with `BURHAN_URL` pointing at the Burhan build being promoted;
5. only move a form into `round_trip_safe` when the real Albayan -> Burhan conversion returns a strict MathObject that current BuTeX can re-import safely.

The ordinary unit tests also assert that internal/output macros and representative parse/build-only commands are not accidentally advertised.
