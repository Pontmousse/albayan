# Stripe donations — Al-Bayan deployment and operations

Issue: #82

Al-Bayan keeps the public donation experience on the journal domain. Stripe handles the sensitive payment controls, payment processing, localized presentment currency, and the authoritative payment record.

## Architecture

```text
/daam-al-bayan (Arabic/RTL Al-Bayan UI)
        │
        ├─ GET /api/v1/public/donations/config
        ├─ POST /api/v1/public/donations/checkout-session
        │        └─ Stripe Checkout Session (mode=payment, ui_mode=elements)
        │              └─ Adaptive Pricing enabled
        │
        ├─ Stripe.js Checkout Elements SDK (locale=ar)
        │        ├─ Currency Selector Element
        │        └─ Payment Element owns card/wallet fields
        │
        └─ /daam-al-bayan/tamam?session_id=...
                 └─ backend retrieves the Checkout Session from Stripe

Stripe webhook
        └─ POST /api/v1/webhooks/stripe
                 ├─ raw-body signature verification
                 └─ optional Arabic confirmation via Resend
                         └─ one minimal local receipt row prevents duplicate emails
```

Stripe remains the source of truth for payment status, amount, currency, donor payment details, Checkout Session IDs, and PaymentIntent IDs. Al-Bayan does not mirror that payment state in its database.

## Product boundaries

- All journal services remain free.
- Donations do not affect submission, peer review, editorial decisions, publication, access, account capabilities, or MCP capabilities.
- This integration is payment-only; it does not create subscriptions.
- It does not enable Stripe Invoicing.
- The journal never receives or stores card numbers or CVC values.
- The acknowledgement email is not described as a tax receipt, charitable receipt, or zakat certificate.

## Currency behaviour

`DONATION_CURRENCY` is the integration/base currency used for the amount selected before the payment controls are initialized. The default is CAD.

Adaptive Pricing is enabled on each Checkout Session. For eligible customers, Stripe infers a relevant presentment currency from the customer's public IP address, converts the amount, and exposes the local choice through the Currency Selector Element. The donor can see the localized total before confirming payment.

The return page and Arabic confirmation email use Stripe's `presentment_details` when available, so they show the currency and amount the donor actually paid rather than assuming the configured base currency.

Adaptive Pricing must also be enabled for Checkout in the Stripe Dashboard. If Stripe can't localize a Session, the configured base currency remains in use.

## Stripe Dashboard setup

Do the setup in **Sandbox** first.

### 1. Branding

In Stripe Branding settings, upload the approved Al-Bayan icon/logo and use the journal's public support details. Stripe-controlled security/provider surfaces (3DS, wallets, required legal notices) must remain intact.

The custom checkout itself is styled through the Stripe Appearance API in the frontend. Do not use DOM/CSS hacks against Stripe's iframe internals.

### 2. Adaptive Pricing

Enable Adaptive Pricing for Checkout in Sandbox and Live mode as appropriate. The Al-Bayan integration marks Checkout as Adaptive-Pricing-ready and renders Stripe's Currency Selector Element near the payment controls.

### 3. Webhook

Create a webhook endpoint:

```text
https://api.albayan-journal.org/api/v1/webhooks/stripe
```

Subscribe only to the paid events used by the Arabic acknowledgement workflow:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

The return page does not depend on webhook-persisted status; it retrieves the Checkout Session directly from Stripe. The webhook is retained only for the optional Arabic acknowledgement email.

Copy the endpoint signing secret into `STRIPE_WEBHOOK_SIGNING_SECRET`.

### 4. Customer emails

Once the Al-Bayan confirmation email is enabled and verified, disable Stripe's automatic **Successful payments** customer email if you want to avoid a duplicate/non-Arabic acknowledgement. Do not suppress provider-required security or authentication communication.

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

`DONATION_MINOR_UNIT_DIVISOR=100` describes the configured base currency amount entered before Checkout is initialized. Stripe handles the local presentment currency after the Session is created.

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

Migration `019_donations` originally introduced local payment-mirror tables. Migration `020_minimize_donations` removes those tables and leaves only:

- `donation_email_receipts`: Checkout Session ID plus the time the Al-Bayan acknowledgement email was sent.

This row exists only because Stripe documents that webhook events can be delivered more than once and live-mode retries can continue for days, while Resend's own idempotency-key retention is shorter. We therefore keep durable state only for the side effect Stripe cannot know about: whether **our** Arabic email was already sent.

No amount, currency, payment status, PaymentIntent ID, donor email, card data, CVC, client secret, API key, or webhook secret is stored in the Al-Bayan database for donations.

If the Arabic acknowledgement email is removed in the future, this receipt table and the Stripe webhook can also be removed; the payment UI and return page can operate from Stripe alone.

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
5. Confirm the Currency Selector/localized total appears for an eligible test location.
6. Complete a successful Stripe test payment.
7. Confirm the return page retrieves the paid Session from Stripe and shows the presentment amount/currency.
8. Confirm one Arabic acknowledgement is sent when an email is supplied.
9. Re-deliver the paid webhook event and confirm it does not send another acknowledgement.
10. Exercise 3DS and declined-card test paths.
11. Confirm no raw provider exception text appears in user-facing UI.

Stripe documents location-formatted test emails such as `test+location_FR@example.com` for simulating Adaptive Pricing from a particular country in Sandbox.

## Going live

Only after sandbox verification:

1. switch both frontend/backend to keys from the same live Stripe account;
2. enable Adaptive Pricing for Checkout and verify the Currency Selector flow;
3. create the production webhook and update its signing secret;
4. confirm the production Al-Bayan branding in Stripe;
5. sync the Arabic Resend template and disable duplicate Stripe successful-payment emails if desired;
6. apply `alembic upgrade head`, deploy the backend, then deploy the frontend;
7. run one low-value live verification and reconcile it in the Stripe Dashboard.

Do not merge deployment/config changes automatically; keep them reviewable.
