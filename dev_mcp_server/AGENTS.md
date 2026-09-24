# Developer MCP agent guidance

This directory contains a **developer-only** MCP connector. It is not the public Al-Bayan authoring MCP server.

When using or extending these tools:

1. Start with `dev_capabilities` before assuming a service, model tier, headless adapter, or browser observation capability is available.
2. Prefer specialized diagnostic tools over generic HTTP access.
3. Run the smallest relevant named regression suite first; use `dev_regression_suites` to discover suites and `dev_run_regression_suite` for bounded execution.
4. For equation bugs, start with `dev_equation_inspect`; use `dev_equation_compare_model_tiers` only when the model tier is part of the hypothesis, and use fixtures/suites for regressions.
5. Treat the fixture corpus as inputs plus metadata, not golden serialized AST snapshots. `known_failure` is descriptive and must never override an observed result.
6. Gather trace IDs and observable stage evidence before assigning likely ownership. A `likely_owning_service` derived from the first failing boundary is a debugging hint, not proof of root cause.
7. Keep deterministic headless BuTeX evidence (`fromMathObjectJson` -> `mathObjectToEditorSession`) distinct from real browser evidence. Use Playwright MCP separately when the problem depends on DOM/UI/MathJax/browser behavior.
8. Playwright is not proxied through the Dev MCP. If browser evidence is required, correlate it with Dev MCP evidence where practical and pass only a bounded browser summary into `dev_investigation_report`.
9. Correlate related diagnostic operations with returned `trace_id` values; never treat a trace ID as authentication or authorization.
10. Inspect `dev_get_trace` for available ordered evidence before assigning a failure to a service, and respect `partial`, `missing_observations`, and unavailable stages when the current source cannot observe downstream internals.
11. Rerun the relevant regression suite after a code change and produce an evidence-oriented `dev_investigation_report` before claiming the regression is fixed.
12. Never invent runtime facts when a service, endpoint, trace, credential, or observation point is unavailable.
13. When blocked, surface the exact `reason`, blockers, missing observations, and human actions to the human developer.
14. Ask the human to add the smallest missing development capability; do not request production credentials as a workaround.
15. Keep tools read-only/non-destructive by default. New mutation/deployment/shell capabilities require separate review and narrow authorization.
16. Never echo tokens, cookies, authorization headers, `.env` contents, full sensitive request bodies, or other secrets in diagnostic output.
17. For remote access, authorize only Clerk users whose server-fetched public metadata contains the boolean flag `developer: true`; do not infer developer access from `role`, email, client identity, or any caller-supplied field.

A useful blocked or partial result is part of the product: the human should know exactly what access, configuration, permission, or instrumentation must be added for the agent to continue.
