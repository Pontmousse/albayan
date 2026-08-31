# Resend / React Email

## Production architecture

```text
React Email source
  → exported HTML with Resend variables
  → published Resend template (`welcome-ar`)
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
EMAIL_ASSET_BASE_URL=https://albayan-journal.org/email

RESEND_WELCOME_TEMPLATE=welcome-ar
```

- Never expose the API key through `NEXT_PUBLIC_*`, logs, template variables,
  API responses, or committed `.env` files.
- `RESEND_WELCOME_TEMPLATE` accepts the published template alias or UUID. The
  stable `welcome-ar` alias is preferred; no `tmpl_` prefix is assumed.
- An empty email configuration disables delivery for local development. Once
  any email-specific value is supplied, startup validation requires the whole
  group. Production URLs must use HTTPS; local HTTP is accepted only with
  `DEV_MODE=true` and a loopback host.
- `FRONTEND_BASE_URL` builds account, manuscript, and action links.
  `EMAIL_ASSET_BASE_URL` is application configuration and is passed into the
  welcome template as `ASSET_BASE_URL`; neither value belongs in Resend's
  environment settings.

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
published welcome template:

```text
USER_NAME
LOGIN_URL
SITE_URL
CONTACT_EMAIL
ASSET_BASE_URL
```

The backend sends exactly these variables. `CONTACT_EMAIL` is derived from the
configured `EMAIL_REPLY_TO` mailbox, so the address is not duplicated in the
service. `email export` renders the triple-brace Resend placeholders; React
Email `PreviewProps` supply readable values only in the local preview.

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
https://albayan-journal.org/email/footer-corner.png
https://albayan-journal.org/email/icons/publish.png
https://albayan-journal.org/email/icons/read.png
https://albayan-journal.org/email/icons/community.png
```

Email clients cannot load React Email's local `/static/` preview paths. The
exported production template must contain only `{{{ASSET_BASE_URL}}}/...` image
URLs, which the test suite verifies.

## Publishing the template

Install the current official Resend CLI and `yq`, then use a Full Access key
dedicated to template administration:

```bash
export RESEND_API_KEY=re_xxxxxxxxxx
cd emails
npm run templates:sync
```

Template administration requires a Full Access key. The deployed backend may
use a different, sending-only key under the same variable name in its own
isolated environment. Keep every key out of shell tracing and CI logs.

The sync workflow exports the React Email source, creates or updates the
`welcome-ar` alias with the declared variables, and publishes the resulting
draft. A missing alias is the only lookup failure that may create a template;
authentication, network, and rate-limit failures stop the workflow.

Useful read-only checks:

```bash
resend doctor
resend templates list --json
resend templates get welcome-ar --json
```

Never commit `RESEND_API_KEY`.
