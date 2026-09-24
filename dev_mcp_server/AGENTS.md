# Developer MCP agent guidance

This directory contains a **developer-only** MCP connector. It is not the public Al-Bayan authoring MCP server.

When using or extending these tools:

1. Treat configured development services as the only allowed runtime targets.
2. Prefer specialized diagnostic tools over generic HTTP access.
3. Correlate related diagnostic operations with the returned `trace_id`; never treat a trace ID as authentication or authorization.
4. Inspect `dev_get_trace` for available ordered evidence before assigning a failure to a service, and respect `partial` / `missing_stages` when the current source cannot observe downstream internals.
5. Use Playwright MCP separately when the question depends on browser/UI/render behavior; do not proxy or reimplement Playwright inside the Dev MCP.
6. Never invent runtime facts when a service, endpoint, trace, credential, or observation point is unavailable.
7. When blocked, surface the exact `reason`, `missing`, `missing_stages`, and `human_action` fields to the human developer.
8. Ask the human to add the smallest missing development capability; do not request production credentials as a workaround.
9. Keep tools read-only/non-destructive by default. New mutation/deployment/shell capabilities require separate review and narrow authorization.
10. Never echo tokens, cookies, authorization headers, `.env` contents, full sensitive request bodies, or other secrets in diagnostic output.
11. For remote access, authorize only Clerk users whose server-fetched public metadata contains the boolean flag `developer: true`; do not infer developer access from `role`, email, client identity, or any caller-supplied field.

A useful blocked or partial result is part of the product: the human should know exactly what access, configuration, or instrumentation must be added for the agent to continue.
