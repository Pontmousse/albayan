# Clerk account-security email templates

This document is the repository source of truth for Al-Bayan's Clerk-owned account-security emails.

The guiding rule is simple:

- Clerk owns authentication/security-event detection and the ordinary account-security notifications.
- Al-Bayan/Resend owns only the explicitly intercepted OTP families: email verification and password reset.
- Never enable a second delivery path for the same event.

## Current production ownership audit

The production Clerk dashboard was reviewed manually on 2026-09-14 together with the repository implementation.

| Clerk template | Production delivery | Owner | Repository implementation |
| --- | --- | --- | --- |
| Account Locked | enabled | Clerk | no matching Resend template |
| Password changed | enabled | Clerk | no matching Resend template |
| Password removed | enabled | Clerk | no matching Resend template |
| Primary email address changed | enabled | Clerk | no matching Resend template |
| Reset password code | disabled in Clerk | Al-Bayan / Resend | `emails/src/auth/PasswordReset.tsx`, alias `password-reset-ar` |
| Sign in from new device | enabled | Clerk | no matching Resend template |

Email verification is intentionally outside this six-template list. It follows the same Al-Bayan/Resend OTP bridge as password reset.

The backend ownership boundary is enforced in `backend/app/services/clerk_email_webhook_service.py`:

- if Clerk says `delivered_by_clerk == true`, Al-Bayan does not send anything;
- if Clerk is not delivering the message, Al-Bayan only handles known verification-code and password-reset slugs;
- every other Clerk email slug is ignored without attempting to parse an OTP.

This prevents an account-security notification from accidentally being re-sent through Resend if a Clerk dashboard setting changes.

## Required production settings

In the production Clerk instance, keep the delivery switches as follows unless a future reviewed change explicitly moves ownership:

- **Account Locked:** on
- **Password changed:** on
- **Password removed:** on
- **Primary email address changed:** on
- **Reset password code:** off
- **Sign in from new device:** on

Do not enable Clerk delivery for **Reset password code** while `password-reset-ar` is active through the Clerk webhook bridge; doing so can bypass the Al-Bayan Arabic template or create inconsistent ownership.

The same no-duplicate rule applies to email-verification OTPs.

## Branding

For Clerk-delivered security messages:

- use the Al-Bayan application name and configured application logo;
- keep the message Arabic-first;
- keep Clerk-provided security/action URLs and buttons intact;
- use RTL-friendly layout where the Clerk editor permits it;
- do not replace Clerk's authentication/security logic with custom backend logic merely for visual consistency;
- do not invent device, location, IP, or session data that Clerk does not actually expose to the template.

If the Clerk template exposes device/session details or a security action button, preserve those variables/components and translate only the surrounding user-facing copy and button label where supported.

## Approved Arabic copy

The copy below is the approved baseline. Clerk-managed dynamic fields/buttons may be retained around it where available.

### Account Locked

**Subject**

> تم قفل حسابكم مؤقتًا في مجلة البيان

**Heading**

> تم قفل الحساب مؤقتًا

**Body**

> بعد عدة محاولات غير ناجحة لتسجيل الدخول، تم قفل حسابكم مؤقتًا لحمايته. يمكنكم المحاولة مجددًا بعد انتهاء مدة القفل. إذا لم تكونوا أنتم من قام بهذه المحاولات، فنوصي بمراجعة أمان حسابكم وتغيير كلمة المرور بعد استعادة الدخول.

Where Clerk provides an unlock/recovery action, keep that action and use a concise Arabic label.

### Password changed

**Subject**

> تم تغيير كلمة مرور حسابكم في مجلة البيان

**Heading**

> تم تغيير كلمة المرور

**Body**

> تم تغيير كلمة مرور حسابكم بنجاح. إذا كنتم أنتم من أجرى هذا التغيير فلا يلزم اتخاذ أي إجراء. إذا لم يكن هذا التغيير من قبلكم، فابدؤوا فورًا باستعادة الحساب ومراجعة إعدادات الأمان.

### Password removed

**Subject**

> تمت إزالة كلمة المرور من حسابكم في مجلة البيان

**Heading**

> تمت إزالة تسجيل الدخول بكلمة المرور

**Body**

> لم يعد تسجيل الدخول بكلمة المرور متاحًا لهذا الحساب، ويمكن استخدام طرق الدخول الأخرى المرتبطة به. إذا لم تقوموا بهذا التغيير، فسجّلوا الدخول بإحدى الطرق المتاحة وراجعوا إعدادات الأمان وطرق الدخول إلى الحساب.

### Primary email address changed

**Subject**

> تم تغيير البريد الإلكتروني الرئيسي لحسابكم في مجلة البيان

**Heading**

> تم تحديث البريد الإلكتروني الرئيسي

**Body**

> تم تحديث البريد الإلكتروني الرئيسي المرتبط بحسابكم. إذا كان هذا التغيير من قبلكم فلا يلزم اتخاذ أي إجراء. إذا لم يكن من قبلكم، فراجعوا حسابكم وطرق الدخول إليه فورًا واستخدموا مسار الاستعادة المتاح عند الحاجة.

### Reset password code

This is **not** a Clerk-delivered production template. Keep Clerk delivery disabled and preserve the existing Al-Bayan/Resend implementation:

- source: `emails/src/auth/PasswordReset.tsx`
- Resend alias: `password-reset-ar`
- subject: `رمز استعادة كلمة المرور في مجلة البيان`

Do not copy the OTP into application logs, issue text, screenshots, analytics, or support notes.

### Sign in from new device

**Subject**

> تسجيل دخول جديد إلى حسابكم في مجلة البيان

**Heading**

> تسجيل دخول من جهاز جديد

**Body**

> تم تسجيل دخول إلى حسابكم من جهاز جديد أو غير معروف. إذا كنتم أنتم من سجل الدخول فلا يلزم اتخاذ أي إجراء. إذا لم تتعرفوا على هذا النشاط، فراجعوا جلسات الحساب وطرق الدخول إليه فورًا وأمّنوا الحساب باستخدام خيارات الأمان المتاحة.

Where Clerk exposes device, browser, approximate location, time, session-revocation, or security-action fields, preserve them. Do not add guessed values.

## Clerk dashboard procedure

For each of the five Clerk-owned notifications:

1. Open the production Clerk application.
2. Go to **Configure → Email & SMS templates → Security**.
3. Open the relevant template.
4. Keep **Delivered by Clerk** enabled.
5. Apply the approved Arabic subject/body above while preserving Clerk's dynamic variables and security actions.
6. Confirm the Al-Bayan application logo/branding is selected where Clerk exposes it.
7. Save the template.

For **Reset password code**, keep **Delivered by Clerk** disabled while the Al-Bayan webhook/Resend path is active.

## Verification checklist

Use test accounts where possible; do not intentionally disrupt a real production account merely to exercise a notification.

Verify:

- Account Locked arrives once, in Arabic, from the intended Clerk delivery path.
- Password changed arrives once and contains the expected security guidance.
- Password removed arrives once and explains that another sign-in method is required.
- Primary email address changed arrives once and gives clear recovery guidance.
- Password reset code arrives exactly once through `password-reset-ar` / Resend.
- Sign in from new device arrives once and retains any legitimate Clerk-provided device/session context.
- No OTP, authorization token, Clerk ticket, or sensitive action URL is written to Albayan application logs.
- Authentication validation, account lockout, session handling, and event detection remain owned by Clerk.

## Change policy

If a future change moves one of these notifications from Clerk to Al-Bayan/Resend, it must update all three places in one reviewed change:

1. Clerk delivery toggle/ownership,
2. the webhook allowlist/handling in `clerk_email_webhook_service.py`, and
3. this document.

Never add a new Resend security-email handler while leaving the corresponding Clerk delivery path enabled unless duplicate delivery is explicitly intended and documented.
