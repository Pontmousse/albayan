# Developer MCP agent guidance

This directory contains a **developer-only** MCP connector. It is not the public Al-Bayan authoring MCP server.

When using or extending these tools:

1. Treat configured development/feature services as the only allowed runtime targets.
2. Prefer specialized diagnostic tools over generic HTTP access.
3. For equation bugs, start with `dev_equation_inspect`; use `dev_equation_compare_model_tiers` only when the model tier is part of the hypothesis, and use fixtures/suites for regressions.
4. Treat the fixture corpus as inputs plus metadata, not golden serialized AST snapshots. `known_failure` is descriptive and must never override an observed result.
5. Keep deterministic headless BuTeX evidence (`fromMathObjectJson` -> `mathObjectToEditorSession`) distinct from real browser evidence. Use Playwright MCP separately when the problem depends on DOM/UI/MathJax/browser behavior.
6. Correlate related diagnostic operations with the returned `trace_id`; never treat a trace ID as authentication or authorization.
7. Inspect `dev_get_trace` for available ordered evidence before assigning a failure to a service, and respect `partial` / `missing_stages` when the current source cannot observe downstream internals.
8. Never invent runtime facts when a service, endpoint, trace, credential, or observation point is unavailable.
9. When blocked, surface the exact `reason`, `missing`, `missing_stages`, and `human_action` fields to the human developer.
10. Ask the human to add the smallest missing development capability; do not request production credentials as a workaround.
11. Keep tools read-only/non-destructive by default. New mutation/deployment/shell capabilities require separate review and narrow authorization.
12. Never echo tokens, cookies, authorization headers, `.env` contents, full sensitive request bodies, or other secrets in diagnostic output.
13. For remote access, authorize only Clerk users whose server-fetched public metadata contains the boolean flag `developer: true`; do not infer developer access from `role`, email, client identity, or any caller-supplied field.

A useful blocked or partial result is part of the product: the human should know exactly what access, configuration, or instrumentation must be added for the agent to continue.
