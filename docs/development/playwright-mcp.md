# Playwright MCP — agent-operated browser testing

[← Development index](README.md) · [Railway infrastructure](railway-infrastructure.md)

**Status: deployed in the Railway `development` environment (observed 2026-10-19).** Playwright MCP is an existing, independently hosted browser automation service, not a feature to implement inside Developer MCP. It lets an AI agent test the Al-Bayan web application **itself**, rather than requesting screenshots, instructions, or manual reproduction from a developer.

## Runtime and access

The Railway project `albayan` deploys `albayan-playwright-mcp` **only in `development`**:

| Item | Observed configuration |
| --- | --- |
| Service | `albayan-playwright-mcp` |
| Image | `mcr.microsoft.com/playwright/mcp:latest` |
| Public service host | `playwright.dev.albayan-journal.org` |
| Browser | Headless Chromium |
| MCP runtime | Microsoft Playwright MCP container, bound to `$PORT` |
| Notable arguments | `--headless --browser chromium --no-sandbox --shared-browser-context --host 0.0.0.0`, with the public service host in `--allowed-hosts` |
| Railway | One replica in `us-east4-eqdc4a`; successful deployment observed |

The Docker image and launch parameters above were read from Railway's current service configuration; they are **not** installation instructions for the application repository. A connected AI client calls its Playwright MCP tools remotely. Client connection/authentication is managed outside Al-Bayan's user-facing authoring MCP. The published host is a network endpoint; **do not infer that merely being on the development environment makes it private or authenticated**. Review network exposure and authentication/access controls before running sensitive tests. A configured `--allowed-hosts` value controls allowed HTTP hostnames; **it is not evidence of caller authentication or isolation**.

## What the AI agent can test

The connected agent can use browser navigation, accessibility/DOM snapshots, clicking and typing, form filling, screenshots, console/error inspection, network request inspection, and viewport changes. This supports direct end-to-end tests of:

- Arabic RTL layout and responsive UI, page navigation, menus and account forms.
- Article editor load/save, BuTeX Document2 interactions, asset placement and revision-conflict messages.
- Structured equations rendered and edited by BuTeX/MathJax, including right-to-left Arabic mathematical presentation.
- Real browser request destinations, HTTP failures and client exceptions.
- A full agent-authored edit appearing in the same browser editor after the normal MCP and FastAPI pipeline processed it.

The availability of these tools **does not imply every test above has already passed**.

## Required development-only procedure

1. Establish a connection to the **separate Playwright MCP**; do not attempt to call it through the Developer MCP proxy.
2. Navigate to <https://dev.albayan-journal.org>. Confirm the final URL is still on the development domain and the expected page is loaded.
3. Inspect an accessibility snapshot and any browser console warnings/errors. Use screenshots for visual evidence, not as the only source of truth for interactions.
4. When testing authenticated flows, use an authorized **development test account**. Keep test credentials out of documentation and tool reports. Never reuse production sessions or customer data.
5. Perform the reproduction via the browser tools: locate an element, click/type/select it, observe the resulting DOM/UI state, and capture the expected postcondition.
6. Inspect network requests as applicable: browser API calls must go to **`api.dev.albayan-journal.org`** and other explicitly approved development origins. Unexpected calls or redirects to production are a **configuration defect**; stop the test rather than silently continuing.
7. For equation bugs, compare browser evidence (MathJax/DOM/editor) with [Developer MCP](developer-mcp.md) trace/fixture results to identify the first failing boundary. A headless BuTeX transformation alone cannot prove browser correctness.
8. After a fix, repeat the browser action and verify the intended result; additionally use the **normal end-user MCP** to validate the actual authoring contract when relevant.

### Suggested focused equation regression

Use `get_math_authoring_capabilities` on the normal MCP, prepare a supported canonical English LaTeX test equation, insert it via a typed `apply_draft_command`, and verify the resulting immutable revision. Then open that article in the *development* browser using Playwright MCP; inspect actual BuTeX editor content, visible Arabic mathematical rendering and console/network behavior. Do not invent block IDs or skip authorization and revision checks.

## Safety and reliability

- The hosted service currently starts with `--shared-browser-context` and `--no-sandbox`. These are **runtime security choices**, not an assurance of isolation. Treat browser state as potentially shared among connected testers; do not assume isolated sessions. Coordinate tests that could interfere, and reset/close dev-only test sessions when appropriate.
- Prefer non-destructive navigation and read-only checks first. Only create/modify **explicitly authorized test data** in development; avoid bulk deletion, irreversible publication or payment actions.
- Do not expose authentication tokens, password fields, cookies or private page contents in public PR comments, screenshots or logs.
- Avoid unrestricted arbitrary-code execution for routine UI inspection; standard browser tools are sufficient for most tasks.
- A temporarily disconnected MCP is a connectivity blocker, **not** evidence that the Al-Bayan app is broken. Retry a bounded check, record the blocker and avoid claiming a full browser regression passed.
- The `:latest` container tag is mutable; for stable reproducible test infrastructure, consider pinning a tested image version/digest in a future infrastructure change. This documentation update does not change it.

## Observation versus configuration (2026-10-19/20)

A direct Playwright MCP navigation reached `https://dev.albayan-journal.org/` with page title **`مجلة البيان`**. Subsequent network inspection could not be completed because the MCP connection became unavailable. This was a **navigation observation only**, not a passing end-to-end article/equation test or a verification of API request routing.

Live `dev_capabilities` independently reported `browser_observation: false` with source `external-playwright-mcp`; Railway nevertheless reported `albayan-playwright-mcp` as deployed successfully. That flag is a **capability hint in Developer MCP**, not the Playwright service's runtime status or an automatic connection between the servers.

Related documentation: [Railway services and environments](railway-infrastructure.md) · [Developer MCP diagnostics](developer-mcp.md) · [Investigations](investigation-workflows.md).
