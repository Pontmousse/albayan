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

BURHAN_COMMIT = "7ad84b2bdfd4c7eb95c2ad7c584b8e2a93207159"
BUTEX_COMMIT = "7f55227b4cf368efb26b937c1729ba2e89eee865"
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
            "arabic_latex_parser/english_converter.py",
            "tests/api/test_parse_equation.py",
            "tests/parser/test_delimiter_coverage.py",
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
            "src/document2/mathBridge.ts",
            "src/document2-cli/execute.ts",
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
    r"\sin",
    r"\cos",
    r"\tan",
    r"\cot",
    r"\sec",
    r"\csc",
    r"\arcsin",
    r"\arccos",
    r"\arctan",
    r"\arccot",
    r"\arcsec",
    r"\arccsc",
    r"\sinh",
    r"\cosh",
    r"\tanh",
    r"\coth",
    r"\sum",
    r"\prod",
    r"\lim",
    r"\arg",
    r"\max",
    r"\min",
    r"\sup",
    r"\inf",
    r"\pi",
    r"\exp",
    r"\ln",
    r"\log",
    r"\det",
]

ATOMIC_OPERATORS = [
    r"\infty",
    r"\times",
    r"\div",
    r"\pm",
    r"\mp",
    r"\neq",
    r"\approx",
    r"\sim",
    r"\mid",
    r"\leq",
    r"\geq",
    r"\coloneqq",
    r"\eqqcolon",
    r"\propto",
    r"\in",
    r"\notin",
    r"\subset",
    r"\supset",
    r"\subseteq",
    r"\supseteq",
    r"\cap",
    r"\cup",
    r"\emptyset",
    r"\ldots",
    r"\cdot",
    r"\cdots",
    r"\vdots",
    r"\ddots",
    r"\Leftrightarrow",
    r"\implies",
    r"\impliedby",
    r"\iff",
    r"\Longrightarrow",
    r"\Longleftarrow",
    r"\to",
    r"\rightleftharpoons",
    r"\leftarrow",
    r"\rightarrow",
    r"\Leftarrow",
    r"\Rightarrow",
    r"\leftharpoonup",
    r"\rightharpoonup",
    r"\leftharpoondown",
    r"\rightharpoondown",
    r"\int",
    r"\iint",
    r"\iiint",
    r"\iiiint",
    r"\oint",
    r"\oiint",
    r"\oiiint",
]

ACCENTS = [
    r"\vec",
    r"\hat",
    r"\tilde",
    r"\dot",
    r"\ddot",
    r"\dddot",
    r"\bar",
    r"\check",
    r"\breve",
    r"\acute",
    r"\grave",
    r"\overline",
    r"\underline",
    r"\overleftarrow",
    r"\overrightarrow",
    r"\overleftrightarrow",
]

SPACING = [r"\!", r"\:", r"\;", r"\quad", r"\qquad"]

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
    "(...) and [...]",
    r"\left( ... \right)",
    r"\left[ ... \right]",
    r"\left\{ ... \right\}",
    r"\left\langle ... \right\rangle",
    r"\left| ... \right|",
    r"\left\vert ... \right\vert",
    r"\left\lvert ... \right\rvert",
    r"\left\| ... \right\|",
    r"\left\Vert ... \right\Vert",
    r"\left\lVert ... \right\rVert",
    r"\left. ... \right.",
    r"\left\lfloor ... \right\rfloor",
    r"\left\lceil ... \right\rceil",
]

# Explicit Burhan input features that are parse/build-capable but are not part of
# the safe AI authoring whitelist because current BuTeX re-import/editing does not
# preserve them reliably.
PARSE_BUILD_ONLY_COMMANDS = [
    r"\theta",
    r"\alpha",
    r"\beta",
    r"\gamma",
    r"\delta",
    r"\epsilon",
    r"\lambda",
    r"\mu",
    r"\rho",
    r"\sigma",
    r"\tau",
    r"\phi",
    r"\psi",
    r"\omega",
    r"\eta",
    r"\zeta",
    r"\chi",
    r"\nabla",
    r"\Delta",
    r"\partial",
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
    r"\mathrm",
    r"\mathsf",
    r"\mathit",
    r"\mathfrak",
    r"\mathbb",
    r"\mathcal",
    r"\mathscr",
    r"\text",
]

PARSE_BUILD_ONLY_ENVIRONMENTS = ["smallmatrix", "cases", "alignedat", "split"]
TOP_LEVEL_ENVIRONMENTS = [
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
    "equation",
    "equation*",
]

INTERNAL_OUTPUT_MACRO_EXAMPLES = [
    r"\ad",
    r"\arsum",
    r"\arprod",
    r"\arlim",
    r"\arsqrt",
    r"\boldarabic",
    r"\arabvec",
    r"\butextakween",
    r"\butexdiwani",
    r"\butexdiwanioutline",
    r"\butexmaghribi",
    r"\unit",
    r"\idx",
    r"\prescript",
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
        "Burhan's permissive parser happens to tokenize it."
    ),
    "preferred_submission": {
        "latex": "Prefer the equation body without outer math delimiters.",
        "display": "Use the compact math token display boolean to select inline/display math.",
        "wrappers_accepted_by_albayan": ["$...$", r"\(...\)", "$$...$$", r"\[...\]"],
    },
    "source_snapshot": SOURCE_SNAPSHOT,
    "round_trip_safe": {
        "commands": {
            "structures": STRUCTURAL_COMMANDS,
            "functions_and_limits": ATOMIC_FUNCTIONS,
            "operators_relations_sets_arrows_integrals": ATOMIC_OPERATORS,
            "accents": ACCENTS,
            "spacing": SPACING,
        },
        "raw_operators": ["+", "-", "=", "*", "/", "<", ">"],
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
        "notes": [
            "Burhan can parse/build these forms, but current BuTeX editor re-import is incomplete or multi-line editing is unsupported.",
            "Top-level multiline math can be stored structurally, but a MathObject with more than one top-level line is not editor-editable.",
            "Burhan also preserves unknown alphabetic commands such as \\foo; that generic passthrough is intentionally not advertised as supported authoring.",
        ],
    },
    "unsupported_or_forbidden": {
        "rule": "For new AI-authored math, every command must appear in round_trip_safe.commands.",
        "internal_output_macro_examples": INTERNAL_OUTPUT_MACRO_EXAMPLES,
        "explicit_parser_rejection_examples": [r"x@", r"\left(x", r"\begin{document}x\end{document}"],
    },
    "normalization_aliases": NORMALIZED_ALIASES,
    "constraints": [
        "Atomic functions/operators/spacing commands take no brace arguments; place operands as following expression nodes.",
        "Accents take exactly one mandatory argument and no optional argument.",
        "\\frac, \\overset, and \\underset take exactly two mandatory arguments.",
        "\\sqrt takes exactly one mandatory radicand and at most one optional root index.",
        "For array, use only l/c/r column alignment letters.",
        "Do not use a top-level row break in AI-authored equations; it creates a multi-line MathObject that the current editor cannot round-trip edit.",
        "Do not depend on generic unknown-command passthrough, LLM normalization, or output-side Arabic macros.",
    ],
    "examples": [
        {"latex": r"\frac{x_1}{\sqrt{1+x^2}}", "display": False},
        {"latex": r"\sum_{i=1}^{n} i^2", "display": True},
        {"latex": r"\int_0^1 x^2\;dx", "display": True},
        {"latex": r"\left\lVert x \right\rVert \leq 1", "display": False},
        {"latex": r"\begin{pmatrix}a&b\\c&d\end{pmatrix}", "display": True},
        {"latex": r"\arg\min_x f(x)", "display": True},
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
    values.extend(ACCENTS)
    values.extend(SPACING)
    return tuple(values)


def burhan_verification_cases() -> list[tuple[str, bool, str]]:
    """One live Albayan->Burhan conversion case for every advertised command/env."""

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
    for command in ACCENTS:
        cases.append((f"{command}{{x}}", False, command))
    for command in SPACING:
        cases.append((f"x{command}y", False, command))

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
