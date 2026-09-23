# Developer MCP agent guidance

This directory contains a **developer-only** MCP connector. It is not the public Al-Bayan authoring MCP server.

When using or extending these tools:

1. Treat configured development services as the only allowed runtime targets.
2. Prefer specialized diagnostic tools over generic HTTP access.
3. Never invent runtime facts when a service, endpoint, trace, credential, or observation point is unavailable.
4. When blocked, surface the exact `reason`, `missing`, and `human_action` fields to the human developer.
5. Ask the human to add the smallest missing development capability; do not request production credentials as a workaround.
6. Keep tools read-only/non-destructive by default. New mutation/deployment/shell capabilities require separate review and narrow authorization.
7. Never echo tokens, cookies, authorization headers, `.env` contents, or other secrets in diagnostic output.
8. For remote access, authorize only Clerk users whose server-fetched public metadata contains the boolean flag `developer: true`; do not infer developer access from `role`, email, client identity, or any caller-supplied field.

A useful blocked result is part of the product: the human should know exactly what access, configuration, or instrumentation must be added for the agent to continue.
