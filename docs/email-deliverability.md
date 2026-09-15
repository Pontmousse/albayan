# Email deliverability and sensitive action links

This document defines the repository rules for transactional email deliverability and enterprise-mail compatibility.

## General rules

- Keep SPF, DKIM, and DMARC valid for the sending domain.
- Prefer first-party Albayan URLs in email content.
- Do not wrap ordinary authenticated application links in extra redirects without a concrete need.
- Do not put secrets, OTPs, bearer tickets, complete sensitive action URLs, or API keys in application logs.
- Use the Resend dashboard and provider SMTP diagnostics as the source of truth for delivery investigation; Albayan does not duplicate Resend's event history in its own database.
- A Resend API `200` means Resend accepted the send request. A later `delivered` event means the recipient mail server accepted the message. Neither guarantees visible Inbox placement.

## Clerk account-security notifications

Clerk remains the authority that detects and validates account-security events, but Al-Bayan/Resend owns delivery of the six security emails listed in [`clerk-security-email-templates.md`](./clerk-security-email-templates.md).

The key invariant is **one delivery owner per event**:

- Clerk **Delivered by Clerk** must be disabled for Account Locked, Password changed, Password removed, Primary email address changed, Reset password code, and Sign in from new device after the custom-delivery rollout is complete;
- Clerk still creates the email event and sends the signed email-created webhook;
- Al-Bayan verifies that webhook, renders the appropriate Arabic React Email template, and sends it through Resend;
- the existing email-verification OTP flow uses the same Al-Bayan/Resend delivery architecture even though it is outside the six security templates documented above;
- if `delivered_by_clerk == true`, the backend deliberately ignores the event so a dashboard configuration mistake cannot generate a duplicate send.

Do not enable Clerk delivery for an event that Al-Bayan is actively delivering through Resend without an explicit reviewed ownership change. Do not add a new Clerk-email webhook handler without updating the corresponding delivery ownership documentation and regression tests.

## Scanner-safe sensitive actions

Any email action that can be consumed or materially advanced by an unauthenticated GET/redirect chain must use a scanner-safe handoff.

The reusable pattern is:

1. The email contains a signed, expiring Albayan handoff URL.
2. A GET renders a first-party confirmation page only; it does not resolve or redirect to the sensitive provider URL.
3. The user must deliberately submit the confirmation form.
4. The backend validates the signed token and current action state, resolves the sensitive destination server-side, and redirects only then.
5. Invalid, expired, revoked, accepted, or otherwise unavailable actions fail on an Albayan page without leaking provider details.

The application-invitation flow under `/tasjil/invitation/...` is the first implementation of this pattern. Future bearer-style email actions should reuse the same signed handoff utility instead of inventing a new redirect mechanism.

Ordinary first-party links, OTP emails, and actions that already require an authenticated user plus server-side identity checks do not need this handoff automatically.

## Enterprise Microsoft 365 troubleshooting

When Resend reports `delivered` but the recipient cannot find the message:

1. Check Junk/Spam and organization quarantine.
2. Open the Resend email details and record the delivery timestamp plus the recipient server's SMTP response, message identifier, internal ID, and hostname when present.
3. Give those identifiers to the recipient organization's mail administrator so they can trace the message after Microsoft accepted custody.
4. Do not assume a successful SMTP `250` response means Inbox placement.
5. Avoid broad permanent allowlisting as a default remedy; investigate authentication, reputation, content, URL scanning, and organization policy first.

## Change checklist

For transactional-email changes:

- verify links are first-party where practical;
- confirm no raw bearer credential is embedded in HTML or text output;
- confirm scanner-like GET requests cannot consume sensitive actions;
- keep a plain-text version where the sending path supports it;
- test important flows with Gmail and an enterprise Microsoft 365 mailbox when practical;
- use Resend diagnostics for delivery failures instead of adding duplicate delivery-history persistence unless a product requirement explicitly needs it.
