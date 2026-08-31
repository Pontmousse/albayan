# Resend / React Email

## Architecture

```text
React Email → Resend Template → FastAPI/Resend API → Recipient
```

- **React Email**: design reusable `.tsx` emails.
- **Resend Templates**: production templates.
- **FastAPI + Resend SDK**: sends production emails.
- **Resend CLI**: development, testing and debugging only.

## Backend delivery configuration

FastAPI uses `RESEND_API_KEY` as its runtime credential for sending email. Give
this credential only the permissions required for delivery; it is not the
template-administration credential used by the synchronization script.

```env
RESEND_API_KEY=re_xxxxx

EMAIL_FROM="مجلة البيان <mail@albayan-journal.org>"
EMAIL_REPLY_TO="مجلة البيان <contact@albayan-journal.org>"

FRONTEND_BASE_URL=https://albayan-journal.org
EMAIL_ASSET_BASE_URL=https://albayan-journal.org/email

RESEND_WELCOME_TEMPLATE=welcome-ar
```

Prefer template aliases (`welcome-ar`) over hardcoded IDs when possible.
Never expose this credential to the browser or use it to run
`sync-resend-templates.sh`.

## Local/CI template synchronization

Template synchronization requires a separate template-administration
credential in `RESEND_TEMPLATE_SYNC_API_KEY`. Configure it in the local shell or
the CI secret store, then run:

```bash
export RESEND_TEMPLATE_SYNC_API_KEY=<template-administration-key>
./emails/sync-resend-templates.sh
```

The script exports that value to `RESEND_API_KEY` only in its own process
because this is the variable name expected by the Resend CLI. It does not accept
a preexisting `RESEND_API_KEY` as a fallback, so the backend runtime/send
credential cannot be used accidentally for template administration.

Do not enable shell tracing (`set -x`) while configuring or running the script,
and never print either credential in local or CI logs.

## Email assets

Store public assets in:

```text
public/email/
├── logo.png
├── header-arch.png
├── divider.png
└── icons/
```

They become publicly accessible at:

```text
https://albayan-journal.org/email/...
```

Email images **must be publicly accessible over HTTPS without authentication**.

## Resend CLI

Useful commands:

```bash
# Check configuration
resend doctor

# Domains
resend domains list

# Templates
resend templates list
resend templates get <alias>
resend templates publish <alias>

# Debugging
resend logs list
resend logs get <id>
```

For agents/CI, use JSON where useful:

```bash
resend templates list --json
resend doctor --json
```

## React Email

Recommended:

```text
emails/
├── components/
│   └── AlbayanLayout.tsx
├── welcome.tsx
├── submission-received.tsx
└── review-status.tsx
```

All emails share:

```tsx
<AlbayanLayout>
  {/* email-specific content */}
</AlbayanLayout>
```

Local development:

```bash
npx react-email@latest resend setup
```

The shared layout is the **template-of-templates**.

## Rule

Never use the CLI from FastAPI for production sending.

```text
Development → React Email + Resend CLI
Production  → FastAPI + Resend API/SDK
```

Never commit `RESEND_API_KEY` or `RESEND_TEMPLATE_SYNC_API_KEY`.
