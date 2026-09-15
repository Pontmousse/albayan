# Resend / React Email

## Production architecture

```text
React Email source
  → exported HTML with Resend variables
  → published Resend template aliases (`welcome-ar`, `decision-ar`, ...)
  → FastAPI sends through the Resend REST API
```

The backend never invokes a CLI. It sends either a published template or raw
HTML through one internal transport function; those two modes are mutually
exclusive because Resend rejects a payload that combines them.

## Backend environment

Configure these server-only application variables together:

```env
RESEND_API_KEY=re_xxxxxxxxxx
EMAIL_FROM="مجلة البيان <mail@albayan-journal.org>"
EMAIL_REPLY_TO="مجلة البيان <support@albayan-journal.org>"

FRONTEND_BASE_URL=https://albayan-journal.org

RESEND_WELCOME_TEMPLATE=welcome-ar
RESEND_APP_INVITATION_TEMPLATE=app-invitation-ar
RESEND_AUTH_VERIFICATION_TEMPLATE=auth-verification-code-ar
RESEND_PASSWORD_RESET_TEMPLATE=password-reset-ar
RESEND_SUBMISSION_RECEIVED_TEMPLATE=submission-received-ar
RESEND_NEW_SUBMISSION_ALERT_TEMPLATE=new-submission-alert-ar
RESEND_EDITOR_ASSIGNED_TEMPLATE=editor-assigned-ar
RESEND_REVIEW_INVITATION_TEMPLATE=review-invitation-ar
RESEND_REVIEWER_ASSIGNED_TEMPLATE=reviewer-assigned-ar
RESEND_REVIEW_REMINDER_TEMPLATE=review-reminder-ar
RESEND_REVIEW_SUBMITTED_TEMPLATE=review-submitted-ar
RESEND_DECISION_TEMPLATE=decision-ar
RESEND_ARTICLE_PUBLISHED_TEMPLATE=article-published-ar
RESEND_UNREAD_NOTIFICATIONS_DIGEST_TEMPLATE=unread-notifications-digest-ar

CLERK_WEBHOOK_SIGNING_SECRET=whsec_xxxxxxxxxx
CLERK_SECRET_KEY=sk_live_xxxxxxxxxx
```

- Never expose the API key through `NEXT_PUBLIC_*`, logs, template variables,
  API responses, or committed `.env` files.
- `RESEND_*_TEMPLATE` values accept published template aliases or UUIDs. Stable
  aliases such as `welcome-ar`, `auth-verification-code-ar`, and
  `review-reminder-ar` are preferred; no `tmpl_` prefix is assumed.
- The five notification-only Clerk security templates use stable aliases owned
  directly by `emails/templates.yaml` and `clerk_security_email_service.py`:
  `account-locked-ar`, `password-changed-ar`, `password-removed-ar`,
  `primary-email-changed-ar`, and `new-device-sign-in-ar`. They intentionally
  do not add five more backend environment variables. Password reset keeps its
  existing `RESEND_PASSWORD_RESET_TEMPLATE=password-reset-ar` setting.
- An empty email configuration disables delivery for local development. Once
  any email-specific value is supplied, startup validation requires the whole
  group. Production URLs must use HTTPS; local HTTP is accepted only with
  `DEV_MODE=true` and a loopback host.
- `FRONTEND_BASE_URL` builds account, manuscript, and action links. Email
  assets are always resolved from its `/email` path and passed to templates as
  `ASSET_BASE_URL`. This value belongs to the backend, not Resend's environment
  settings.

Resend owns the API key, verified sending domain, and published templates. The
application owns sender/reply-to identities, template references, frontend
links, and public asset URLs.

`support@albayan-journal.org` is the receiving inbox humans monitor. Resend
can send from `mail@albayan-journal.org` once the domain is verified, even if
that mailbox is only a forwarding alias. If the provider supports aliases, keep
`mail@` and optional legacy `contact@` forwarding to `support@` so direct
replies do not get lost.

## Template variables

`templates.yaml` is the source of truth for the variables required by the
published templates.

Welcome:

```text
USER_NAME
LOGIN_URL
SITE_URL
CONTACT_EMAIL
ASSET_BASE_URL
```

Application invitation:

```text
INVITATION_URL
RECIPIENT_NAME
RECIPIENT_EMAIL
EXPIRES_TEXT
SITE_URL
CONTACT_EMAIL
ASSET_BASE_URL
```

Auth verification code and password reset:

```text
OTP_CODE
RECIPIENT_EMAIL
SITE_URL
CONTACT_EMAIL
ASSET_BASE_URL
```

Clerk security notifications (`account-locked-ar`, `password-changed-ar`,
`password-removed-ar`, `primary-email-changed-ar`, `new-device-sign-in-ar`):

```text
RECIPIENT_EMAIL
DATE_TEXT
SITE_URL
CONTACT_EMAIL
ASSET_BASE_URL
```

These five notifications deliberately start with the stable information needed
for safe delivery. Do not invent device, IP, location, browser, or security-
action values. Add Clerk metadata only after its production webhook payload has
been verified and the additional fields are covered by tests.

Editorial and notification templates:

```text
submission-received-ar:
ARTICLE_TITLE, ARTICLE_URL, SUBMITTED_TEXT, VERSION_NUMBER, SITE_URL,
CONTACT_EMAIL, ASSET_BASE_URL

new-submission-alert-ar:
ARTICLE_TITLE, AUTHOR_NAME, ARTICLE_URL, SITE_URL, CONTACT_EMAIL,
ASSET_BASE_URL

editor-assigned-ar:
ARTICLE_TITLE, ARTICLE_URL, SITE_URL, CONTACT_EMAIL, ASSET_BASE_URL

review-invitation-ar:
ARTICLE_TITLE, ROLE_LABEL, INVITATION_URL, EXPIRES_TEXT, DUE_TEXT,
SITE_URL, CONTACT_EMAIL, ASSET_BASE_URL

reviewer-assigned-ar:
ARTICLE_TITLE, REVIEW_URL, DUE_TEXT, SITE_URL, CONTACT_EMAIL,
ASSET_BASE_URL

review-reminder-ar:
ARTICLE_TITLE, REVIEW_URL, DUE_TEXT, REMINDER_TEXT, SITE_URL,
CONTACT_EMAIL, ASSET_BASE_URL

review-submitted-ar:
ARTICLE_TITLE, REVIEWER_NAME, REPORT_URL, SITE_URL, CONTACT_EMAIL,
ASSET_BASE_URL

decision-ar:
ARTICLE_TITLE, DECISION_TEXT, ARTICLE_URL, NEXT_STEP, SITE_URL,
CONTACT_EMAIL, ASSET_BASE_URL

article-published-ar:
ARTICLE_TITLE, ARTICLE_URL, SITE_URL, CONTACT_EMAIL, ASSET_BASE_URL

unread-notifications-digest-ar:
UNREAD_COUNT, NOTIFICATIONS_URL, SITE_URL, CONTACT_EMAIL, ASSET_BASE_URL
```

The backend sends exactly the variables declared for each template.
`CONTACT_EMAIL` is derived from the configured `EMAIL_REPLY_TO` mailbox, so
the address is not duplicated in the service. `email export` renders the
triple-brace Resend placeholders; React Email `PreviewProps` supply readable
values only in the local preview.

`RECIPIENT_NAME` has the neutral fallback `ضيف مجلة البيان`. Keep this fallback
when updating the published invitation template so an older backend can continue
to send safely during a staged rollout.

## Public email assets

Editable source assets live in `emails/assets/`. Keep the deployed copies in
sync with:

```bash
cd emails
npm run assets:sync
npm run assets:check
```

The sync command writes the same canonical manifest to:

```text
emails/src/static/       # React Email preview
frontend/public/email/   # Next.js production hosting
```

Next.js therefore serves the production files without authentication at:

```text
https://albayan-journal.org/email/logo.png
https://albayan-journal.org/email/header-arch.png
https://albayan-journal.org/email/divider.png
https://albayan-journal.org/email/pattern.png
https://albayan-journal.org/email/footer-corner-left.png
https://albayan-journal.org/email/footer-corner-right.png
https://albayan-journal.org/email/icons/publish.png
https://albayan-journal.org/email/icons/read.png
https://albayan-journal.org/email/icons/community.png
```

Email clients cannot load React Email's local `/static/` preview paths. The
exported production template must contain only `{{{ASSET_BASE_URL}}}/...` image
URLs, which the test suite verifies.

## Publishing the templates

Install the current official Resend CLI and Mike Farah `yq` v4 (the unrelated
Python `yq` package is not compatible), then use a Full Access key dedicated to
template administration. The official Node.js CLI installation is
`npm install -g resend-cli`.

Run the package tests before publishing, then sync every declared alias:

```bash
cd emails
npm ci
npm test

export RESEND_API_KEY=re_xxxxxxxxxx
npm run templates:sync
```

Template administration requires a Full Access key. The deployed backend may
use a different, sending-only key under the same variable name in its own
isolated environment. Keep every key out of shell tracing and CI logs.

The sync workflow exports the React Email source, creates or updates every
alias in `templates.yaml` with the declared variables, and publishes the
resulting drafts. A missing alias is the only lookup failure that may create a
template; authentication, network, and rate-limit failures stop the workflow.

After the Clerk security-email change, verify these aliases are present and
published before turning Clerk delivery off:

```text
account-locked-ar
password-changed-ar
password-removed-ar
primary-email-changed-ar
password-reset-ar
new-device-sign-in-ar
```

Useful read-only checks:

```bash
resend doctor
resend templates list --json
resend templates get password-reset-ar --json
resend templates get account-locked-ar --json
```

Never commit `RESEND_API_KEY`.

## Clerk security-email rollout

The complete ownership matrix and Dashboard instructions live in
`docs/clerk-security-email-templates.md`. The safe order is:

1. Deploy the backend webhook handlers while current Clerk delivery is still on.
2. Run the tests and `npm run templates:sync`; confirm all six Resend aliases
   above are published.
3. Verify Clerk's production webhook points to
   `https://api.albayan-journal.org/api/v1/webhooks/clerk` and that the backend
   has the matching `CLERK_WEBHOOK_SIGNING_SECRET`.
4. Disable **Delivered by Clerk** for the six security templates one at a time.
5. Trigger each flow with a test account and confirm exactly one corresponding
   Resend message arrives before moving to the next template.

There is no need to paste Arabic template copy into Clerk for these six emails;
the source of truth is the React Email source plus the published Resend aliases.

## Safe rollout and mobile acceptance

Because the invitation template gains a variable and two public assets, use this
order and avoid sending application invitations during the short rollout window:

1. Deploy the frontend public assets and verify both footer-corner URLs return
   PNG files over HTTPS.
2. Run `npm test` in `emails/`, then publish the templates with
   `npm run templates:sync`.
3. Run `alembic upgrade head`, then deploy the backend and frontend application
   code.
4. Send one invitation to a controlled address and verify the CTA opens
   `/tasjil` with exactly one `__clerk_ticket` query parameter.
5. Check the received message in at least one narrow iOS or Android mail client:
   no horizontal scrolling, full CTA visibility, readable OTP blocks, stacked
   welcome features, and distinct mirrored footer corners.

The templates use one responsive HTML document, not a separate mobile version.
The export test enforces a viewport tag, the mobile breakpoint, one occurrence
of every action URL, and the absence of CSS image mirroring and recipient-facing
vendor names.
