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

## Common Greek and standard symbols

The contract now exposes a general `round_trip_safe.commands.standard_symbols` group. It is not an `\alpha` / `\beta` special case.

The advertised set is the reviewed intersection of Burhan's `GREEK_SYMBOL_COMMANDS` mapping registry and BuTeX 7.2.x's tested `STANDARD_COMMANDS` editable fallback registry:

```text
\alpha  \beta  \gamma  \delta  \epsilon  \eta  \theta
\lambda \mu    \rho    \sigma  \tau      \phi  \chi
\psi    \omega \zeta   \nabla  \Delta    \partial
```

Recent upstream changes are what make this possible:

- Burhan structures resolved Arabic LaTeX mapping fragments as real `CommandObject` nodes instead of embedding command strings in `CharObject.expr`.
- Burhan's reverse converter handles command-valued mappings and normalizes equivalent Arabic font wrappers generically; it does not special-case Greek letters.
- BuTeX 7.2.x imports every command in its standard-command compatibility registry as an editable `standardCommand` node, preserves scripts, rendering, save/reopen, and structured export, while still rejecting genuinely unknown commands.

These standard fallback symbols are intentionally separate from BuTeX's Arabic authoring toolbar/custom macro registries. The editor may show a non-blocking warning for a standard fallback command; that warning does not make the MathObject non-editable.

## Reviewed source revisions

The snapshot in `backend/app/services/math_authoring_capabilities.py` is pinned to the reviewed development revisions:

- Burhan `drghaliasri/burhan3.0` commit `db27bdd64102b03d3bb1ab86063b042958bfd94a`;
- BuTeX `drghaliasri/butex` commit `9287812c93fa0e34f7d269887edee60b0fe7ff1d`.

The Burhan revision includes the structured Arabic mapping work, command-valued reverse mapping, and equivalent font-wrapper normalization. The key reviewed files include `commands.py`, `arabic_json_normalizer.py`, `english_converter.py`, and their regression tests.

The BuTeX revision includes the 7.2.x standard-command fallback and font-wrapper import normalization. The key round-trip boundary is `src/document/mathEditorAdapter.ts`; `src/editor/standardCommands.ts` is the compatibility registry and `test/standard_commands.test.ts` exercises every registered command.

Before promoting this Albayan snapshot to an environment that uses different Burhan/BuTeX revisions, align or re-review the pinned upstream service versions.

## Updating the contract

When Burhan or BuTeX math support changes:

1. review the pinned source files and recent relevant merge requests rather than documentation alone;
2. update the whitelist conservatively and bump the pinned commit(s);
3. for a command family, derive the advertised set from the actual supported upstream registries rather than adding one-off exceptions;
4. ensure every advertised command and environment still has a case in `burhan_verification_cases()`;
5. run `backend/tests/test_math_authoring_capabilities.py` with `BURHAN_URL` pointing at the Burhan build being promoted;
6. only move a form into `round_trip_safe` when the real Albayan -> Burhan conversion returns a strict MathObject that current BuTeX can re-import safely.

The ordinary unit tests also assert that internal/output macros and representative parse/build-only commands are not accidentally advertised.
