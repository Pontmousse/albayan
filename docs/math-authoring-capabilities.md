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

Burhan #7 and BuTeX #23 have landed. On 2026-10-06 the persisted **normal Al-Bayan MCP** path plus the development browser validated transpose, number-set roles, exact differential `\mathrm{d}`, and simple `\mathsf` unit atoms. Those scoped forms are now advertised under `round_trip_safe.commands.semantic_roles`. The `\mathtt` named-variable convention remains documented but is not yet advertised safe because the real browser path preserved unmapped names such as `var` and `sin` in Latin instead of producing the intended Arabic translation.

The validated forms include:

```latex
A^\top + T
R + \mathbb{R}
N + \mathbb{N} + 3\mathsf{N}
d + \frac{\mathrm{d}f}{\mathrm{d}x}
m + 3\mathsf{m}
```

The safe scope is deliberately narrow:

- `\mathbb` is advertised only for `N, Z, Q, R, C, H`.
- `\mathrm` is advertised only as exact `\mathrm{d}`.
- `\mathtt` is one atomic multi-character Latin variable name, but it is **not currently in `round_trip_safe`**. The code is designed to call the selected Burhan model for an unmapped atomic name; the persisted dev browser result instead kept `var`/`sin` in Latin, so that behavior still needs to be resolved before promotion.
- `\mathsf` is one unit atom and is round-trip safe. Compound unit expressions may combine unit atoms with safe raw operators such as `3\mathsf{m}/\mathsf{s}`.
- Raw `/`, `<`, and `>` are again in `round_trip_safe`: Burhan's reverse converter now applies the inverse of its Arabic-side mirroring, and BuTeX normalizes the structured `\backslash` divide command into the editable divide role instead of displaying the command name literally.
- Existing legacy `\unit{...}` input remains supported by the stack but is not the preferred AI authoring convention.

The strict Document2 math-node schema accepts bounded optional `source_latex` provenance emitted by Burhan; Burhan-only `arabic_unit` metadata is removed at the Al-Bayan projection boundary instead of becoming editor state. There are no equation profiles, migrations, or new semantic macros. `contract_version: 1` remains response bookkeeping, not an equation version.


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

- Burhan `drghaliasri/burhan3.0` commit `396d6c1c0068ad01b2f4a19d4dc411deb2f0af17` (merged MR !20 / develop);
- BuTeX `drghaliasri/butex` commit `b509c02c3e07230efa48519f4e66fbcc44499c9d` (current MR !43 head).

The Burhan revision includes the standard semantic authoring work for `\top`, number systems, exact differential `\mathrm{d}`, atomic `\mathtt` names, and `\mathsf` units, plus merged inverse normalization of Arabic presentation operators during reverse conversion. The key reviewed files now also include `nodes.py`, `llm_utils.py`, `english_converter.py`, and `tests/api/test_standard_math_authoring.py`.

The BuTeX revision includes the structured import/export work for the same forms plus the divide/unit browser fixes. The key round-trip boundary is `src/document/mathEditorAdapter.ts`; `src/editor/divideOperator.ts` normalizes Burhan's structured `\backslash` divide spelling, while `src/register/passthrough.ts` renders units as upright MathJax text and the editor marks unit atoms visibly.

Before promoting this Albayan snapshot to an environment that uses different Burhan/BuTeX revisions, align or re-review the pinned upstream service versions.

## Updating the contract

When Burhan or BuTeX math support changes:

1. review the pinned source files and recent relevant merge requests rather than documentation alone;
2. update the whitelist conservatively and bump the pinned commit(s);
3. for a command family, derive the advertised set from the actual supported upstream registries rather than adding one-off exceptions;
4. ensure every advertised command and environment still has a case in `burhan_verification_cases()`;
5. run `backend/tests/test_math_authoring_capabilities.py` with `BURHAN_URL` pointing at the Burhan build being promoted;
6. only move a form into `round_trip_safe` when the real Albayan -> Burhan conversion returns a strict MathObject that current BuTeX can re-import safely;
7. when a command is only safe in a semantic subset (for example exact `\mathrm{d}`), advertise the scoped form and its constraints rather than the generic wrapper.

The ordinary unit tests also assert that internal/output macros and representative parse/build-only commands are not accidentally advertised.
