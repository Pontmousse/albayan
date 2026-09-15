# Clerk account-security email delivery

This document is the repository source of truth for the six Clerk account-security emails used by Al-Bayan.

## Architecture

Clerk remains the authentication and security authority, but Clerk does **not** deliver these six emails directly.

```text
security event
  -> Clerk detects/validates it
  -> Clerk creates the corresponding email event
  -> Delivered by Clerk = OFF
  -> signed email.created / emails.created webhook
  -> Al-Bayan FastAPI verifies the webhook
  -> Al-Bayan selects its Arabic React Email template
  -> Resend delivers the message
```

The rule is one delivery owner per email. For the six templates below, the delivery owner is Al-Bayan/Resend. Clerk owns only event detection, authentication state, OTP generation, account lockout, session/security state, and the signed webhook event.

Clerk documents this as the supported custom-delivery model: disabling **Delivered by Clerk** on a template prevents Clerk from sending it while still allowing the email-created webhook to provide the information needed for custom delivery.

## Six templates

| Clerk template | Clerk webhook slug | Al-Bayan React Email | Resend alias | Delivered by Clerk |
| --- | --- | --- | --- | --- |
| Account Locked | `account_locked` | `emails/src/auth/AccountLocked.tsx` | `account-locked-ar` | OFF |
| Password changed | `password_changed` | `emails/src/auth/PasswordChanged.tsx` | `password-changed-ar` | OFF |
| Password removed | `password_removed` | `emails/src/auth/PasswordRemoved.tsx` | `password-removed-ar` | OFF |
| Primary email address changed | `primary_email_address_changed` | `emails/src/auth/PrimaryEmailChanged.tsx` | `primary-email-changed-ar` | OFF |
| Reset password code | `reset_password_code` | `emails/src/auth/PasswordReset.tsx` | `password-reset-ar` | OFF |
| Sign in from new device | `new_device_sign_in` | `emails/src/auth/NewDeviceSignIn.tsx` | `new-device-sign-in-ar` | OFF |

Email verification is not part of the six-item Clerk screen above, but its existing `verification_code` flow uses the same webhook -> Al-Bayan -> Resend architecture.

The backend also accepts the legacy/current reset-password slug aliases already present in `clerk_email_webhook_service.py`, so an existing production reset flow does not depend on one spelling.

## Backend ownership

`backend/app/services/clerk_email_webhook_service.py` is the signed Clerk-event router.

It must:

- ignore any message where `delivered_by_clerk == true` so a Dashboard mistake cannot cause a second send;
- accept only explicitly supported Clerk email slugs;
- require `otp_code` only for OTP templates;
- never require or parse OTP metadata for notification-only security templates;
- derive the Resend idempotency key from the Clerk email event ID;
- never log OTPs, sensitive action URLs, or bearer credentials.

`backend/app/services/clerk_security_email_service.py` owns the five notification-only mappings to their stable Resend aliases. Password reset keeps using the existing `send_password_reset_email()` path.

The five security aliases are intentionally stable source-controlled aliases from `emails/templates.yaml`; they do not require five additional backend environment variables.

## Template content

All five new notification templates use the same Al-Bayan email shell, Arabic/RTL copy, Hijri send date, public Al-Bayan email assets, and the configured support address.

### Account Locked

Subject: `تم قفل حسابكم مؤقتًا في مجلة البيان`

The message explains that repeated unsuccessful sign-in attempts caused a temporary lock and advises the user to secure the account if the attempts were not theirs. It does not guess the lock duration.

### Password changed

Subject: `تم تغيير كلمة مرور حسابكم في مجلة البيان`

The message confirms the change and tells the user to secure the account immediately if they did not initiate it.

### Password removed

Subject: `تمت إزالة كلمة المرور من حسابكم في مجلة البيان`

The message explains that password sign-in is no longer available and another configured sign-in method is required.

### Primary email address changed

Subject: `تم تغيير البريد الإلكتروني الأساسي في مجلة البيان`

The message confirms the account-level change and gives concise recovery/security guidance.

### Reset password code

Subject: `رمز استعادة كلمة المرور في مجلة البيان`

This is the existing `password-reset-ar` OTP template. Clerk generates the code; Al-Bayan receives it in the signed webhook metadata and sends it through Resend. Never log or persist the OTP.

### Sign in from new device

Subject: `تسجيل دخول إلى حسابكم في مجلة البيان من جهاز جديد`

The first implementation deliberately does not invent device, IP, browser, location, or session-revocation values. It states that Clerk detected a successful sign-in from an unrecognized device and gives recovery guidance. If production webhook testing later confirms stable Clerk metadata fields that we want to surface, add them in a separate reviewed change with tests.

## One-time Resend setup

The new React Email templates are declared in `emails/templates.yaml` and marked `publish: true`.

Before disabling Clerk delivery in production, publish/sync the templates to Resend from this branch (or after merge):

```bash
cd emails
npm ci
npm test

# Use a Full Access Resend key that can administer templates.
export RESEND_API_KEY=re_...
npm run templates:sync
```

The sync script exports the React Email HTML, creates or updates every alias from `templates.yaml`, declares the template variables, and publishes the drafts.

After the command succeeds, verify at least these aliases exist and are published in Resend:

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
```

Do not put the Full Access template-administration key in the repository. The deployed backend continues using its normal server-side `RESEND_API_KEY` for sending.

## Clerk Dashboard production setup

Do this only **after** the Resend templates are published and the backend containing the webhook handlers is deployed.

### 1. Verify the webhook endpoint

In Clerk Dashboard -> **Webhooks**, verify the production endpoint points to:

```text
https://api.albayan-journal.org/api/v1/webhooks/clerk
```

and is subscribed to the email-created event. Clerk documentation has used both `email.created` and `emails.created`; the Al-Bayan endpoint accepts both spellings.

Confirm the endpoint's signing secret is configured in the backend as:

```text
CLERK_WEBHOOK_SIGNING_SECRET=whsec_...
```

The existing password-reset flow already depends on this endpoint, so do not create a second competing Clerk webhook endpoint unless there is a deliberate reason.

### 2. Disable Clerk delivery for all six

Go to Clerk Dashboard -> **Emails / Email & SMS templates -> Security** and open each template individually.

Set **Delivered by Clerk = OFF** for:

- Account Locked
- Password changed
- Password removed
- Primary email address changed
- Reset password code
- Sign in from new device

There is no need to paste the Arabic email body into Clerk. The Arabic source of truth is the React Email code in this repository and the published Resend templates.

### 3. Do not change Clerk security behavior

Turning email delivery off does not move account locking, new-device detection, password state, primary-email state, OTP generation, or authentication validation into Al-Bayan. Clerk continues to own those security behaviors; only delivery is delegated.

## Safe rollout order

To avoid silently dropping security mail during rollout:

1. Deploy the PR backend first while current Clerk delivery is still enabled.
2. Sync/publish the six Resend templates and verify the aliases exist.
3. Verify the production Clerk webhook endpoint succeeds for an email-created test event.
4. Turn **Delivered by Clerk** off for one template at a time.
5. Trigger the corresponding action on a test account and verify exactly one Al-Bayan/Resend message arrives.
6. Continue with the next template only after the previous one is confirmed.

Password reset is already on the Al-Bayan/Resend path; keep it off in Clerk throughout.

## Verification checklist

Use test accounts where practical.

Verify:

- Account Locked -> one `account-locked-ar` email through Resend.
- Password changed -> one `password-changed-ar` email through Resend.
- Password removed -> one `password-removed-ar` email through Resend.
- Primary email address changed -> one `primary-email-changed-ar` email through Resend.
- Reset password code -> one `password-reset-ar` email with the Clerk-generated OTP.
- Sign in from new device -> one `new-device-sign-in-ar` email through Resend.
- Clerk's own delivery is off for all six, so no duplicate message arrives.
- Clerk webhook attempts show success (`2xx`).
- Resend shows the matching send attempt/template alias.
- No OTP, secret, Clerk ticket, or sensitive URL appears in application logs.

## Change policy

Do not add a new Clerk email slug or change one of these ownership rules without updating the webhook tests and this document in the same reviewed change.
