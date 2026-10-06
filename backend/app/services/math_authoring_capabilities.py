"""Deterministic AI-facing canonical LaTeX authoring contract.

Burhan deliberately preserves unknown command tokens, so parser acceptance alone is
not a useful authoring contract. This snapshot is the conservative intersection of:

* Burhan canonical-English parsing/conversion at BURHAN_COMMIT;
* Albayan's strict Document2 MathObject bridge; and
* BuTeX editor re-import support at BUTEX_COMMIT.

When either upstream changes, review the source files listed in ``SOURCE_SNAPSHOT``,
update this snapshot, and run the live Burhan contract test with ``BURHAN_URL`` set.
Do not broaden the whitelist merely because Burhan's generic command parser accepts a
command: every advertised form must remain safe through the Albayan insertion path.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Reviewed upstream revisions for the 2026-10-06 semantic-authoring contract.
# The base semantic roles were persisted/browser validated; the mirrored-operator
# and editor-display follow-up fixes are pinned explicitly below.
BURHAN_COMMIT = "396d6c1c0068ad01b2f4a19d4dc411deb2f0af17"
BUTEX_COMMIT = "d0d59b08d6cd1e6d63c205175d731d8863bad4c7"
ROW_SEPARATOR = chr(92) * 2

SOURCE_SNAPSHOT: dict[str, Any] = {
    "burhan": {
        "repository": "drghaliasri/burhan3.0",
        "commit": BURHAN_COMMIT,
        "files": [
            "arabic_latex_parser/latex_parser.py",
            "arabic_latex_parser/commands.py",
            "arabic_latex_parser/nodes.py",
            "arabic_latex_parser/base_node.py",
            "arabic_latex_parser/equation_processor.py",
            "arabic_latex_parser/arabic_json_normalizer.py",
            "arabic_latex_parser/english_converter.py",
            "arabic_latex_parser/llm_utils.py",
            "tests/api/test_parse_equation.py",
            "tests/api/test_reverse_command_mappings.py",
            "tests/api/test_convert_to_english.py",
            "tests/parser/test_delimiter_coverage.py",
            "tests/parser/test_structured_arabic_commands.py",
            "tests/api/test_standard_math_authoring.py",
            "tests/api/test_prescanning_semantic_guards.py",
        ],
    },
    "butex": {
        "repository": "drghaliasri/butex",
        "commit": BUTEX_COMMIT,
        "files": [
            "src/document/mathEditorAdapter.ts",
            "src/editor/atomicCommands.ts",
            "src/editor/atomicCommandsOperators.ts",
            "src/editor/accentCommands.ts",
            "src/editor/standardCommands.ts",
            "src/editor/display/delimiter.ts",
            "src/document2/mathBridge.ts",
            "src/document2-cli/execute.ts",
            "test/standard_commands.test.ts",
            "test/vertical_delimiter_import.test.ts",
            "test/standard_math_roundtrip.test.ts",
            "src/editor/divideOperator.ts",
            "src/editor/display/base.ts",
            "src/editor/styles.ts",
            "src/register/passthrough.ts",
            "src/rtl-css.ts",
            "test/register.compatMacros.test.ts",
            "test/editor_css.test.ts",
        ],
    },
}

STRUCTURAL_COMMANDS = [
    {
        "command": r"\frac",
        "mandatory_args": 2,
        "optional_args": 0,
        "form": r"\frac{numerator}{denominator}",
    },
    {
        "command": r"\sqrt",
        "mandatory_args": 1,
        "optional_args": "0_or_1",
        "form": r"\sqrt{radicand} or \sqrt[index]{radicand}",
    },
    {
        "command": r"\overset",
        "mandatory_args": 2,
        "optional_args": 0,
        "form": r"\overset{annotation}{base}",
    },
    {
        "command": r"\underset",
        "mandatory_args": 2,
        "optional_args": 0,
        "form": r"\underset{annotation}{base}",
    },
]

ATOMIC_FUNCTIONS = [
    r"\sin", r"\cos", r"\tan", r"\cot", r"\sec", r"\csc",
    r"\arcsin", r"\arccos", r"\arctan", r"\arccot", r"\arcsec", r"\arccsc",
    r"\sinh", r"\cosh", r"\tanh", r"\coth",
    r"\sum", r"\prod", r"\lim", r"\arg", r"\max", r"\min", r"\sup", r"\inf",
    r"\pi", r"\exp", r"\ln", r"\log", r"\det",
]

ATOMIC_OPERATORS = [
    r"\infty", r"\times", r"\div", r"\pm", r"\mp", r"\neq", r"\approx",
    r"\sim", r"\mid", r"\leq", r"\geq", r"\coloneqq", r"\eqqcolon",
    r"\propto", r"\in", r"\notin", r"\subset", r"\supset", r"\subseteq",
    r"\supseteq", r"\cap", r"\cup", r"\emptyset", r"\ldots", r"\cdot",
    r"\cdots", r"\vdots", r"\ddots", r"\Leftrightarrow", r"\implies",
    r"\impliedby", r"\iff", r"\Longrightarrow", r"\Longleftarrow", r"\to",
    r"\rightleftharpoons", r"\leftarrow", r"\rightarrow", r"\Leftarrow",
    r"\Rightarrow", r"\leftharpoonup", r"\rightharpoonup",
    r"\leftharpoondown", r"\rightharpoondown", r"\int", r"\iint",
    r"\iiint", r"\iiiint", r"\oint", r"\oiint", r"\oiiint",
]

# General standard-symbol set supported by BOTH:
# - Burhan GREEK_SYMBOL_COMMANDS; and
# - BuTeX 7.2.x STANDARD_COMMANDS editable fallback.
# Keep this as a capability group, not per-symbol special cases.
STANDARD_SYMBOL_COMMANDS = [
    r"\alpha",
    r"\beta",
    r"\gamma",
    r"\delta",
    r"\epsilon",
    r"\eta",
    r"\theta",
    r"\lambda",
    r"\mu",
    r"\rho",
    r"\sigma",
    r"\tau",
    r"\phi",
    r"\chi",
    r"\psi",
    r"\omega",
    r"\zeta",
    r"\nabla",
    r"\Delta",
    r"\partial",
]

ACCENTS = [
    r"\vec", r"\hat", r"\tilde", r"\dot", r"\ddot", r"\dddot", r"\bar",
    r"\check", r"\breve", r"\acute", r"\grave", r"\overline", r"\underline",
    r"\overleftarrow", r"\overrightarrow", r"\overleftrightarrow",
]

SPACING = [r"\!", r"\:", r"\;", r"\quad", r"\qquad"]

# Scoped semantic forms validated through the persisted normal MCP path and the
# development browser on 2026-10-06. These are intentionally narrower than
# generic LaTeX font-wrapper support.
SEMANTIC_ROLE_COMMANDS = [
    {
        "command": r"\top",
        "meaning": "transpose",
        "form": r"A^\top",
        "constraints": ["Use as the transpose symbol in a script; bare T remains a variable."],
    },
    {
        "command": r"\mathbb",
        "meaning": "number_set",
        "form": r"\mathbb{N}",
        "allowed_args": ["N", "Z", "Q", "R", "C", "H"],
        "constraints": ["Exactly one advertised number-set letter as the mandatory argument."],
    },
    {
        "command": r"\mathrm",
        "meaning": "differential",
        "form": r"\mathrm{d}",
        "allowed_args": ["d"],
        "constraints": [r"Only exact \mathrm{d} is advertised by this semantic convention."],
    },
    {
        "command": r"\mathsf",
        "meaning": "unit",
        "form": r"\mathsf{m}",
        "argument": r"one unit token matching [A-Za-z]+, \\[A-Za-z]+, or Ω",
        "constraints": [
            "One unit atom per wrapper.",
            r"Compound unit expressions may combine safe unit atoms with safe raw operators, e.g. 3\mathsf{m}/\mathsf{s}.",
        ],
    },
]

RAW_OPERATORS = ["+", "-", "=", "*", "/", "<", ">"]

SAFE_INTERNAL_ENVIRONMENTS = [
    {"name": "matrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {"name": "pmatrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {"name": "bmatrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {"name": "Bmatrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {"name": "vmatrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {"name": "Vmatrix", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
    {
        "name": "array",
        "columns": "required column spec using only l, c, r",
        "rows": "use environment_syntax.row_separator",
    },
    {"name": "aligned", "columns": "inferred", "rows": "use environment_syntax.row_separator"},
]

SAFE_DELIMITERS = [
    {"left": "(", "right": ")", "form": "(...)"},
    {"left": "[", "right": "]", "form": "[...]"},
    {"left": r"\left(", "right": r"\right)", "form": r"\left( ... \right)"},
    {"left": r"\left[", "right": r"\right]", "form": r"\left[ ... \right]"},
    {"left": r"\left\{", "right": r"\right\}", "form": r"\left\{ ... \right\}"},
    {"left": r"\left\langle", "right": r"\right\rangle", "form": r"\left\langle ... \right\rangle"},
    {"left": r"\left|", "right": r"\right|", "form": r"\left| ... \right|"},
    {"left": r"\left\vert", "right": r"\right\vert", "form": r"\left\vert ... \right\vert"},
    {"left": r"\left\lvert", "right": r"\right\rvert", "form": r"\left\lvert ... \right\rvert"},
    {"left": r"\left\|", "right": r"\right\|", "form": r"\left\| ... \right\|"},
    {"left": r"\left\Vert", "right": r"\right\Vert", "form": r"\left\Vert ... \right\Vert"},
    {"left": r"\left\lVert", "right": r"\right\rVert", "form": r"\left\lVert ... \right\rVert"},
    {"left": r"\left\lfloor", "right": r"\right\rfloor", "form": r"\left\lfloor ... \right\rfloor"},
    {"left": r"\left\lceil", "right": r"\right\rceil", "form": r"\left\lceil ... \right\rceil"},
]

PARSE_BUILD_ONLY_COMMANDS = [
    r"\not",
    r"\backslash",
    r"\Longleftrightarrow",
    r"\sech",
    r"\csch",
    r"\arcsinh",
    r"\arccosh",
    r"\arctanh",
    r"\arccoth",
    r"\arcsech",
    r"\arccsch",
    r"\binom",
    r"\overbrace",
    r"\underbrace",
    r"\mathbf",
    r"\bfseries",
    r"\mathtt",
    r"\mathit",
    r"\mathfrak",
    r"\mathcal",
    r"\mathscr",
    r"\text",
]

PARSE_BUILD_ONLY_ENVIRONMENTS = ["smallmatrix", "cases", "alignedat", "split"]
PARSE_BUILD_ONLY_DELIMITERS = [
    {
        "left": r"\left.",
        "right": r"\right.",
        "form": r"\left. ... \right.",
        "reason": "Burhan supports the invisible delimiter, but the current BuTeX editor delimiter renderer does not recognize '.'.",
    }
]
TOP_LEVEL_ENVIRONMENTS = [
    "align", "align*", "gather", "gather*", "multline", "multline*",
    "eqnarray", "eqnarray*", "equation", "equation*",
]

INTERNAL_OUTPUT_MACRO_EXAMPLES = [
    r"\ad", r"\arsum", r"\arprod", r"\arlim", r"\arsqrt", r"\boldarabic",
    r"\arabvec", r"\butextakween", r"\butexdiwani", r"\butexdiwanioutline",
    r"\butexmaghribi", r"\unit", r"\idx", r"\prescript",
]

NORMALIZED_ALIASES = [
    {"input": "argmin", "normalized": r"\arg\min", "author": r"\arg\min"},
    {"input": r"\argmin", "normalized": r"\arg\min", "author": r"\arg\min"},
    {"input": "argmax", "normalized": r"\arg\max", "author": r"\arg\max"},
    {"input": r"\argmax", "normalized": r"\arg\max", "author": r"\arg\max"},
]

CAPABILITIES: dict[str, Any] = {
    "contract_version": 1,
    "canonical_input": True,
    "representation": "canonical_english_latex",
    "instruction": (
        "Before authoring new equations, use only round_trip_safe syntax below. "
        "Send ordinary canonical LaTeX through the compact Document2 math token. "
        "Never emit Burhan/BuTeX Arabic-side or output-only macros. Any command not "
        "advertised in round_trip_safe is outside the AI authoring contract, even if "
        "Burhan's permissive parser happens to tokenize it. "
        "preferred_submission.semantic_conventions describes the five agreed forms. "
        "Transpose, number sets, the exact differential, and simple unit atoms are advertised "
        "under round_trip_safe.commands.semantic_roles after persisted MCP + browser validation. "
        r"\mathtt remains outside round_trip_safe until the intended Arabic translation of "
        "unmapped atomic names is verified. Follow the per-form constraints rather than treating "
        "the underlying font wrappers as generic safe syntax."
    ),
    "preferred_submission": {
        "latex": "Prefer the equation body without outer math delimiters.",
        "display": "Use the compact math token display boolean to select inline/display math.",
        "wrappers_accepted_by_albayan": ["$...$", r"\(...\)", "$$...$$", r"\[...\]"],
        "semantic_conventions": {
            "transpose": r"Use A^\top for transpose, never A^T; bare T is a variable.",
            "number_sets": (
                r"Use \mathbb{N}, \mathbb{Z}, \mathbb{Q}, \mathbb{R}, "
                r"\mathbb{C}, \mathbb{H} for naturals, integers, rationals, reals, "
                "complex numbers, quaternions. Bare letters are variables; D is not a number set."
            ),
            "differential": r"Use exact \mathrm{d}, never bare d for a differential; bare d is a variable.",
            "named_variable": (
                r"Use \mathtt{var} for one atomic multi-character Latin variable, with scripts outside, "
                r"e.g. \mathtt{var}_0. Do not use it for compound expressions. "
                r"\mathtt{sin} is a named variable, whereas \sin is the function."
            ),
            "unit": (
                r"Use \mathsf{m} for a unit, through the existing \unit resolver and its "
                r"known-unit/model/fallback behavior. Existing \unit input remains supported; "
                r"\mathsf{N} is a unit, not \mathbb{N} or the variable N."
            ),
        },
    },
    "source_snapshot": SOURCE_SNAPSHOT,
    "round_trip_safe": {
        "commands": {
            "structures": STRUCTURAL_COMMANDS,
            "functions_and_limits": ATOMIC_FUNCTIONS,
            "operators_relations_sets_arrows_integrals": ATOMIC_OPERATORS,
            "standard_symbols": STANDARD_SYMBOL_COMMANDS,
            "semantic_roles": SEMANTIC_ROLE_COMMANDS,
            "accents": ACCENTS,
            "spacing": SPACING,
        },
        "raw_operators": RAW_OPERATORS,
        "scripts": [
            "Use ^ and _ with one atom or a braced group, e.g. x^2, x_{i+1}.",
            "Scripts may contain other round_trip_safe constructs.",
        ],
        "delimiters": SAFE_DELIMITERS,
        "internal_environments": SAFE_INTERNAL_ENVIRONMENTS,
        "environment_syntax": {
            "cell_separator": "&",
            "row_separator": ROW_SEPARATOR,
            "nesting": "Different supported environments may be nested; avoid nesting the same environment name inside itself.",
        },
    },
    "accepted_but_not_round_trip_safe": {
        "commands": PARSE_BUILD_ONLY_COMMANDS,
        "internal_environments": PARSE_BUILD_ONLY_ENVIRONMENTS,
        "top_level_environments": TOP_LEVEL_ENVIRONMENTS,
        "delimiters": PARSE_BUILD_ONLY_DELIMITERS,
        "notes": [
            "Burhan can parse/build these forms, but current BuTeX editor re-import is incomplete or multi-line editing is unsupported.",
            "Common Greek/symbol commands are advertised separately under round_trip_safe.commands.standard_symbols because Burhan maps them and BuTeX 7.2.x imports them as editable standardCommand nodes.",
            "Top-level multiline math can be stored structurally, but a MathObject with more than one top-level line is not editor-editable.",
            r"\mathtt preserves atomic-name identity, but the development browser E2E kept unmapped names such as var/sin in Latin instead of producing the intended Arabic translation.",
            r"Burhan also preserves unknown alphabetic commands such as \foo; that generic passthrough is intentionally not advertised as supported authoring.",
        ],
    },
    "unsupported_or_forbidden": {
        "rule": "For new AI-authored math, every command must appear in round_trip_safe.commands and every raw operator must appear in round_trip_safe.raw_operators.",
        "internal_output_macro_examples": INTERNAL_OUTPUT_MACRO_EXAMPLES,
        "explicit_parser_rejection_examples": [r"x@", r"\left(x", r"\begin{document}x\end{document}"],
    },
    "normalization_aliases": NORMALIZED_ALIASES,
    "constraints": [
        "Atomic functions/operators/spacing commands take no brace arguments; place operands as following expression nodes.",
        "Standard-symbol commands take no brace arguments; scripts may be attached normally.",
        "Accents take exactly one mandatory argument and no optional argument.",
        r"\frac, \overset, and \underset take exactly two mandatory arguments.",
        r"\sqrt takes exactly one mandatory radicand and at most one optional root index.",
        "For array, use only l/c/r column alignment letters.",
        "Do not use a top-level row break in AI-authored equations; it creates a multi-line MathObject that the current editor cannot round-trip edit.",
        r"Do not use \mathtt for new AI-authored math yet; unmapped atomic names did not receive the intended Arabic translation in the persisted browser E2E.",
        "Do not depend on generic unknown-command passthrough, LLM normalization, or output-side Arabic macros.",
    ],
    "examples": [
        {"latex": r"\frac{x_1}{\sqrt{1+x^2}}", "display": False},
        {"latex": r"\sum_{i=1}^{n} i^2", "display": True},
        {"latex": r"\frac{\partial f}{\partial x}", "display": True},
        {"latex": r"\left\lVert x \right\rVert \leq 1", "display": False},
        {"latex": r"\begin{pmatrix}a&b\\c&d\end{pmatrix}", "display": True},
        {"latex": r"\arg\min_x f(x)", "display": True},
        {"latex": r"A^\top + T", "display": False},
        {"latex": r"N + \mathbb{N} + 3\mathsf{N}", "display": False},
        {"latex": r"d + \frac{\mathrm{d}f}{\mathrm{d}x}", "display": False},
        {"latex": r"m + 3\mathsf{m}", "display": False},
        {"latex": r"3\mathsf{m}/\mathsf{s}", "display": False},
    ],
}


def get_math_authoring_capabilities() -> dict[str, Any]:
    """Return an isolated deterministic copy of the authoring snapshot."""

    return deepcopy(CAPABILITIES)


def advertised_round_trip_commands() -> tuple[str, ...]:
    """Flatten the command whitelist for contract tests and drift verification."""

    values: list[str] = []
    values.extend(item["command"] for item in STRUCTURAL_COMMANDS)
    values.extend(ATOMIC_FUNCTIONS)
    values.extend(ATOMIC_OPERATORS)
    values.extend(STANDARD_SYMBOL_COMMANDS)
    values.extend(item["command"] for item in SEMANTIC_ROLE_COMMANDS)
    values.extend(ACCENTS)
    values.extend(SPACING)
    return tuple(values)


def burhan_verification_cases() -> list[tuple[str, bool, str]]:
    """One live Albayan->Burhan conversion case for every advertised syntax item."""

    cases: list[tuple[str, bool, str]] = []
    structure_examples = {
        r"\frac": r"\frac{x}{y}",
        r"\sqrt": r"\sqrt[3]{x}",
        r"\overset": r"\overset{a}{x}",
        r"\underset": r"\underset{a}{x}",
    }
    for command in (item["command"] for item in STRUCTURAL_COMMANDS):
        cases.append((structure_examples[command], False, command))
    for command in ATOMIC_FUNCTIONS:
        cases.append((f"{command} x", False, command))
    for command in ATOMIC_OPERATORS:
        cases.append((f"x {command} y", False, command))
    for command in STANDARD_SYMBOL_COMMANDS:
        cases.append((command, False, command))

    semantic_examples = {
        r"\top": r"A^\top + T",
        r"\mathbb": r"N + \mathbb{N} + 3\mathsf{N}",
        r"\mathrm": r"d + \frac{\mathrm{d}f}{\mathrm{d}x}",
        r"\mathsf": r"m + 3\mathsf{m}",
    }
    for item in SEMANTIC_ROLE_COMMANDS:
        command = item["command"]
        cases.append((semantic_examples[command], False, command))

    # Same implementation path for all six advertised number-set arguments.
    for symbol in "ZQRCH":
        cases.append((rf"{symbol} + \mathbb{{{symbol}}}", False, f"semantic_number_set:{symbol}"))

    for command in ACCENTS:
        cases.append((f"{command}{{x}}", False, command))
    for command in SPACING:
        cases.append((f"x{command}y", False, command))
    for operator in RAW_OPERATORS:
        cases.append((f"x{operator}y", False, f"raw_operator:{operator}"))
    cases.append((r"x_{i+1}^2", False, "scripts:^_"))

    for index, delimiter in enumerate(SAFE_DELIMITERS):
        cases.append((delimiter["form"].replace("...", "x"), False, f"delimiter:{index}"))

    env_examples = {
        "matrix": r"\begin{matrix}a&b\\c&d\end{matrix}",
        "pmatrix": r"\begin{pmatrix}a&b\\c&d\end{pmatrix}",
        "bmatrix": r"\begin{bmatrix}a&b\\c&d\end{bmatrix}",
        "Bmatrix": r"\begin{Bmatrix}a&b\\c&d\end{Bmatrix}",
        "vmatrix": r"\begin{vmatrix}a&b\\c&d\end{vmatrix}",
        "Vmatrix": r"\begin{Vmatrix}a&b\\c&d\end{Vmatrix}",
        "array": r"\begin{array}{cc}a&b\\c&d\end{array}",
        "aligned": r"\begin{aligned}a&=b\\c&=d\end{aligned}",
    }
    for environment in SAFE_INTERNAL_ENVIRONMENTS:
        name = environment["name"]
        cases.append((env_examples[name], True, f"environment:{name}"))
    return cases
