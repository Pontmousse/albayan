# Resend / React Email

## Architecture

```text
React Email → Resend Template → FastAPI/Resend API → Recipient
```

- **React Email**: design reusable `.tsx` emails.
- **Resend Templates**: production templates.
- **FastAPI + Resend SDK**: sends production emails.
- **Resend CLI**: development, testing and debugging only.

## Environment

```env
RESEND_API_KEY=re_xxxxx

EMAIL_FROM="مجلة البيان <mail@albayan-journal.org>"
EMAIL_REPLY_TO="مجلة البيان <contact@albayan-journal.org>"

FRONTEND_BASE_URL=https://albayan-journal.org
EMAIL_ASSET_BASE_URL=https://albayan-journal.org/email

RESEND_WELCOME_TEMPLATE=welcome-ar
```

Prefer template aliases (`welcome-ar`) over hardcoded IDs when possible.

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

Never commit `RESEND_API_KEY`.