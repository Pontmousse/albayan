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

## Five simple semantic conventions

`preferred_submission.semantic_conventions` describes the single agreed convention:

| Meaning | Authoring syntax |
| --- | --- |
| Transpose | `A^\top`; never `A^T` for this meaning. Bare `T` is a variable. |
| Number systems | `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{R}`, `\mathbb{C}`, `\mathbb{H}`. Bare letters are variables; `H` means quaternions here and `D` is not a number system. |
| Differential | Exact `\mathrm{d}`; bare `d` is a variable. |
| Multi-character variable | `\mathtt{var}`, scripts outside (`\mathtt{var}_0`). Use it for one atomic multi-character Latin variable, not a compound expression. `\mathtt{sin}` is a name; `\sin` is a function. |
| Unit | `\mathsf{m}`, using Burhan's existing `\unit` resolver, known-unit tables and model/fallback logic. Keep existing `\unit` support. |

These are conventions for this stack: `\mathtt` and `\mathsf` are ordinary LaTeX font commands, not universal declarations of variable/unit semantics.

This Al-Bayan change can be reviewed before [Burhan #7](https://gitlab.com/drghaliasri/burhan3.0/-/work_items/7) and [BuTeX #23](https://gitlab.com/drghaliasri/butex/-/work_items/23). The five forms are **not yet advertised as `round_trip_safe`**. The tool explicitly explains that verification is pending; clients must keep using the tested whitelist. The input schemas already accept their LaTeX unchanged. Existing storage, conversion, mappings and read-back remain in place. There are no equation profiles, runtime guards, migrations or new macros. `contract_version: 1` remains response bookkeeping, not an equation version.

After the upstream work lands, verify through **normal MCP**: insert with `apply_draft_command`, reload persisted Document2, edit/save/reopen in BuTeX, then read with `get_draft_equations`. English read-back must retain the intended roles, wrappers and current edited values:

```latex
A^\top + T
R+\mathbb{R}                 % also test N, Z, Q, C, H inside mathbb
d+\frac{\mathrm{d}f}{\mathrm{d}x}
\mathtt{var}_0
\mathtt{foo}
\mathtt{sin}+\sin x
m+3\mathsf{m}
N+\mathbb{N}+3\mathsf{N}
3\unit{m}
```

Use fixed variable mappings for deterministic tests; separately exercise an unmapped name with the free tier and a provider failure. Editing `var` to `foo` must read back `foo`, not a cached original name. Dev MCP diagnostics and schema acceptance alone do not prove this round trip. Once verified, update the existing whitelist and reviewed source revisions; forward any minimal upstream source identity only if the actual output requires it.


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
