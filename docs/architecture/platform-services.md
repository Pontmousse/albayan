# Other product services

[← Architecture index](README.md) · **Implemented product boundaries**

The article editor is only one part of Al-Bayan. This page replaces completed feature implementation plans with a short map of the **current code**.

## Notifications, issues and editorial workflow

- [`notifications.py`](../../backend/app/routers/notifications.py): authenticated user notification lists, pagination, unread counts, mark-one-read and mark-all-read actions. [`notification_service.py`](../../backend/app/services/notification_service.py) and [`notification.py`](../../backend/app/models/notification.py) own backend delivery/read state.
- [`issues.py`](../../backend/app/routers/issues.py): logged-in reporting/feedback, optional image uploads, issue detail, upvotes and related management. [`issue.py`](../../backend/app/models/issue.py) stores issue/vote/image metadata. Admin moderation is distinct from normal end-user actions.
- [`invitations.py`](../../backend/app/routers/invitations.py), [`reviews.py`](../../backend/app/routers/reviews.py), [`editor.py`](../../backend/app/routers/editor.py) and [`admin.py`](../../backend/app/routers/admin.py): controlled human editorial/review and invitation flows. No agent should infer permission from mere route discovery.

## Identity, email and sensitive actions

- Clerk owns authentication/security-event verification; Al-Bayan owns its server-side application permissions and selected Arabic email delivery through Resend.
- Backend email services/webhooks are under [`services/`](../../backend/app/services/) and [`routers/webhooks.py`](../../backend/app/routers/webhooks.py). Sensitive links and one-time codes require deliberate handling.
- See [Email deliverability](../development/email-deliverability.md) and [Clerk security emails](../development/clerk-security-email.md) for the maintained **operational** rules. They belong in Development because changing delivery requires configuration/runbook work, not a new domain architecture.

## Public donations

The public donation endpoints under `/api/v1/public/donations` expose configuration, checkout-session creation and status retrieval; [`donation_service.py`](../../backend/app/services/donation_service.py) integrates with Stripe. Stripe is the payment processor/source of truth; Al-Bayan should not persist raw payment credentials or pretend to replace Stripe's transaction ledger. An internal donation email receipt model prevents duplicate emails.

The operational setup and safe sandbox/live rollout guide is [Development: Stripe donations](../development/stripe-donations.md).

## Developer boundary

The development-only diagnostics and Playwright browser tool are not public publishing features. See [MCP boundaries](mcp.md) and [Railway environments](../development/railway-infrastructure.md).
