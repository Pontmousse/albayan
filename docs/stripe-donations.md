# Stripe donations — Al-Bayan deployment and operations

Issue: #82

Al-Bayan keeps the public donation experience on the journal domain. Stripe handles only the sensitive payment controls and payment processing.

## Architecture

```text
/daam-al-bayan (Arabic/RTL Al-Bayan UI)
        │
        ├─ GET /api/v1/public/donations/config
        ├─ POST /api/v1/public/donations/checkout-session
        │        └─ Stripe Checkout Session (mode=payment, ui_mode=elements)
        │
        ├─ Stripe.js Checkout Elements SDK (locale=ar)
        │        └─ Payment Element owns card/wallet fields
        │
        └─ /daam-al-bayan/tamam?session_id=...
                 └─ reads Al-Bayan's persisted donation status

Stripe webhook
        └─ POST /api/v1/webhooks/stripe
                 ├─ raw-body signature verification
                 ├─ event-id idempotency
                 ├─ donation status update
                 └─ optional Arabic confirmation via Resend
```

The browser return page is presentation only. The signed Stripe webhook is the authoritative path that marks a donation paid and triggers the confirmation email.

## Product boundaries

- All journal services remain free.
- Donations do not affect submission, peer review, editorial decisions, publication, access, account capabilities, or MCP capabilities.
- This integration is one-time payment only; it does not create subscriptions.
- It does not enable Stripe Invoicing.
- The journal never receives or stores card numbers or CVC values.
- The acknowledgement email is not described as a tax receipt, charitable receipt, or zakat certificate.

## Stripe Dashboard setup

Do the setup in **Sandbox** first.

### 1. Branding

In Stripe Branding settings, upload the approved Al-Bayan icon/logo and use the journal's public support details. Stripe-controlled security/provider surfaces (3DS, wallets, required legal notices) must remain intact.

The custom checkout itself is styled through the Stripe Appearance API in the frontend. Do not use DOM/CSS hacks against Stripe's iframe internals.

### 2. Webhook

Create a webhook endpoint:

```text
https://api.albayan-journal.org/api/v1/webhooks/stripe
```

Subscribe only to the events this flow understands:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `checkout.session.expired`

The initial Checkout Session filters payment methods to `card`; Apple Pay / Google Pay can still appear through the card Payment Element on supported devices. The async events are handled defensively if payment-method configuration changes later.

Copy the endpoint signing secret into `STRIPE_WEBHOOK_SIGNING_SECRET`.

### 3. Customer emails

Once the Al-Bayan confirmation email is enabled and verified, disable Stripe's automatic **Successful payments** customer email to avoid a duplicate/non-Arabic acknowledgement. Do not suppress provider-required security or authentication communication.

## Environment variables

### Frontend

```env
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

The publishable key is intentionally browser-visible.

### Backend

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SIGNING_SECRET=whsec_...
DONATION_CURRENCY=cad
DONATION_MIN_AMOUNT_MINOR=500
DONATION_MAX_AMOUNT_MINOR=500000
DONATION_MINOR_UNIT_DIVISOR=100
```

`STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SIGNING_SECRET` must never be exposed through `NEXT_PUBLIC_*`.

`DONATION_MINOR_UNIT_DIVISOR=100` means the API amounts are stored as cents for CAD. If the configured currency uses a different minor-unit exponent, update this divisor to match before enabling payments.

### Optional Resend template

The backend can send a safe inline Arabic acknowledgement without a dedicated template. For the reviewed React Email version, sync `donation-received-ar` and set:

```env
RESEND_DONATION_RECEIVED_TEMPLATE=donation-received-ar
```

This is in addition to the existing complete Resend configuration group.

## Database migration

Apply:

```bash
cd backend
alembic upgrade head
```

Migration `016_donations` creates:

- `donations`: minimal operational payment state and optional donor email;
- `stripe_webhook_events`: processed Stripe event IDs for idempotency.

Neither table contains card numbers, CVC, Checkout client secrets, API keys, or webhook secrets.

## Email template

The React Email template is:

```text
emails/src/donations/DonationReceived.tsx
```

It is registered as `donation-received-ar` in `emails/templates.yaml`. Sync/publish it using the repository's existing template workflow before setting `RESEND_DONATION_RECEIVED_TEMPLATE` in production.

## Sandbox verification

Before switching to live keys:

1. Open `/daam-al-bayan` on desktop and mobile.
2. Verify the free-services/editorial-independence statement is visible before payment.
3. Test a preset amount and a custom amount.
4. Confirm the Payment Element renders Arabic labels and fits the RTL page.
5. Complete a successful Stripe test payment.
6. Confirm the webhook marks the row `paid` and sends at most one Arabic acknowledgement.
7. Re-deliver the same webhook event and confirm it does not create another donation/email.
8. Exercise 3DS and declined-card test paths.
9. Confirm the return page never treats a browser redirect alone as proof of payment.
10. Confirm no raw Stripe exception text appears in user-facing UI.

## Going live

Only after sandbox verification:

1. switch both frontend/backend to keys from the same live Stripe account;
2. create the production webhook and update its signing secret;
3. confirm the production Al-Bayan branding in Stripe;
4. sync the Arabic Resend template and disable duplicate Stripe successful-payment emails if desired;
5. deploy backend migration/config first, then frontend;
6. run one low-value live verification and reconcile it in the Stripe Dashboard.

Do not merge deployment/config changes automatically; keep them reviewable.
