"use client";

import Script from "next/script";
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  createDonationCheckout,
  formatDonationAmount,
  getDonationConfig,
  parseDonationAmount,
  type DonationConfig,
} from "@/lib/donations";

type CheckoutSessionSnapshot = {
  canConfirm: boolean;
  total: { total: { amount: string } };
};

type CheckoutConfirmResult =
  | { type: "success" }
  | { type: "error"; error?: unknown };

type CheckoutUpdateEmailResult = {
  error?: unknown;
};

type CheckoutActions = {
  confirm(options?: { email?: string }): Promise<CheckoutConfirmResult>;
  updateEmail(email: string | null): Promise<CheckoutUpdateEmailResult>;
};

type CheckoutLoadActionsResult =
  | { type: "success"; actions: CheckoutActions }
  | { type: "error"; error?: unknown };

type CheckoutElement = {
  mount(target: HTMLElement | string): void;
  destroy?: () => void;
  unmount?: () => void;
};

type CheckoutInstance = {
  on(event: "change", callback: (session: CheckoutSessionSnapshot) => void): void;
  createPaymentElement(options?: {
    layout?: { type: "accordion" | "tabs" };
    wallets?: { link?: "auto" | "never" };
  }): CheckoutElement;
  createCurrencySelectorElement(): CheckoutElement;
  loadActions(): Promise<CheckoutLoadActionsResult>;
};

type StripeClient = {
  initCheckoutElementsSdk(options: {
    clientSecret: string | Promise<string>;
    elementsOptions?: {
      appearance?: Record<string, unknown>;
      loader?: "auto" | "always" | "never";
    };
    adaptivePricing?: { allowed: boolean };
  }): CheckoutInstance;
};

declare global {
  interface Window {
    Stripe?: (
      publishableKey: string,
      options?: { locale?: "ar" | "auto" },
    ) => StripeClient;
  }
}

const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ?? "";
const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

const appearance = {
  theme: "stripe",
  variables: {
    colorPrimary: "#24584a",
    colorBackground: "#fffef9",
    colorText: "#17231c",
    colorDanger: "#b42318",
    borderRadius: "12px",
    spacingUnit: "4px",
    fontFamily: "Arial, sans-serif",
  },
  rules: {
    ".Input": {
      border: "1px solid #d8d1bd",
      boxShadow: "none",
    },
    ".Input:focus": {
      border: "1px solid #24584a",
      boxShadow: "0 0 0 2px rgba(36, 88, 74, 0.12)",
    },
    ".Label": {
      color: "#33443b",
    },
  },
};

export function DonationCheckout() {
  const [config, setConfig] = useState<DonationConfig | null>(null);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customMode, setCustomMode] = useState(false);
  const [customAmount, setCustomAmount] = useState("");
  const [email, setEmail] = useState("");
  const [emailSynced, setEmailSynced] = useState(false);
  const [emailSyncing, setEmailSyncing] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [stripeLoaded, setStripeLoaded] = useState(false);
  const [checkoutReady, setCheckoutReady] = useState(false);
  const [canConfirm, setCanConfirm] = useState(false);
  const [displayTotal, setDisplayTotal] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const currencySelectorHost = useRef<HTMLDivElement>(null);
  const paymentElementHost = useRef<HTMLDivElement>(null);
  const actionsRef = useRef<CheckoutActions | null>(null);

  useEffect(() => {
    let active = true;
    getDonationConfig()
      .then((next) => {
        if (!active) return;
        setConfig(next);
        setSelectedAmount(next.preset_amounts_minor[1] ?? next.preset_amounts_minor[0] ?? null);
      })
      .catch(() => {
        if (active) setError("خدمة المساهمة غير متاحة مؤقتاً.");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (
      !stripeLoaded ||
      !clientSecret ||
      !paymentElementHost.current ||
      !currencySelectorHost.current
    ) return;
    if (!publishableKey || !window.Stripe) {
      setError("خدمة المساهمة غير متاحة مؤقتاً.");
      return;
    }

    setCheckoutReady(false);
    setCanConfirm(false);
    setEmailSynced(false);
    setEmailSyncing(false);
    setEmailError(null);
    actionsRef.current = null;
    paymentElementHost.current.replaceChildren();
    currencySelectorHost.current.replaceChildren();

    const stripe = window.Stripe(publishableKey, { locale: "ar" });
    const checkout = stripe.initCheckoutElementsSdk({
      clientSecret,
      elementsOptions: { appearance, loader: "auto" },
      adaptivePricing: { allowed: true },
    });
    checkout.on("change", (session) => {
      setCanConfirm(session.canConfirm);
      setDisplayTotal(session.total.total.amount);
    });

    const currencySelectorElement = checkout.createCurrencySelectorElement();
    currencySelectorElement.mount(currencySelectorHost.current);

    const paymentElement = checkout.createPaymentElement({
      layout: { type: "accordion" },
      wallets: { link: "never" },
    });
    paymentElement.mount(paymentElementHost.current);

    let active = true;
    checkout
      .loadActions()
      .then((result) => {
        if (!active) return;
        if (result.type === "success") {
          actionsRef.current = result.actions;
          setCheckoutReady(true);
        } else {
          setError("تعذّر تجهيز وسيلة الدفع. حاول مجدداً.");
        }
      })
      .catch(() => {
        if (active) setError("تعذّر تجهيز وسيلة الدفع. حاول مجدداً.");
      });

    return () => {
      active = false;
      actionsRef.current = null;
      setCheckoutReady(false);
      setEmailSynced(false);
      setEmailSyncing(false);
      currencySelectorElement.unmount?.();
      currencySelectorElement.destroy?.();
      paymentElement.unmount?.();
      paymentElement.destroy?.();
    };
  }, [clientSecret, stripeLoaded]);

  const amountMinor = (() => {
    if (!config) return null;
    if (customMode) return parseDonationAmount(customAmount, config.minor_unit_divisor);
    return selectedAmount;
  })();

  const amountIsValid =
    config !== null &&
    amountMinor !== null &&
    amountMinor >= config.min_amount_minor &&
    amountMinor <= config.max_amount_minor;

  async function startCheckout() {
    if (!config || !amountIsValid || amountMinor === null) {
      setError("أدخل مقدار مساهمة صالحاً ضمن الحدود الموضحة.");
      return;
    }
    setError(null);
    setStarting(true);
    try {
      const checkout = await createDonationCheckout(amountMinor);
      setClientSecret(checkout.client_secret);
    } catch {
      setError("تعذّر بدء عملية المساهمة. حاول مجدداً.");
    } finally {
      setStarting(false);
    }
  }

  async function syncEmailToCheckout() {
    const normalizedEmail = email.trim();
    if (!EMAIL_PATTERN.test(normalizedEmail)) {
      setEmailSynced(false);
      setEmailError("أدخل بريداً إلكترونياً صالحاً لإتمام الدفع.");
      return;
    }

    const actions = actionsRef.current;
    if (!actions || !checkoutReady) {
      setEmailSynced(false);
      return;
    }

    setEmailError(null);
    setEmailSyncing(true);
    try {
      const result = await actions.updateEmail(normalizedEmail);
      if (result.error) {
        setEmailSynced(false);
        setEmailError("تعذّر التحقق من البريد الإلكتروني. راجعه ثم حاول مجدداً.");
        return;
      }
      setEmailSynced(true);
    } catch {
      setEmailSynced(false);
      setEmailError("تعذّر التحقق من البريد الإلكتروني. حاول مجدداً.");
    } finally {
      setEmailSyncing(false);
    }
  }

  async function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedEmail = email.trim();
    if (!EMAIL_PATTERN.test(normalizedEmail)) {
      setEmailSynced(false);
      setEmailError("أدخل بريداً إلكترونياً صالحاً لإتمام الدفع.");
      return;
    }
    if (!actionsRef.current || !checkoutReady || !canConfirm || !displayTotal || !emailSynced) {
      setError("انتظر حتى يكتمل تجهيز وسيلة الدفع والتحقق من البريد الإلكتروني.");
      return;
    }

    setError(null);
    setConfirming(true);
    try {
      const result = await actionsRef.current.confirm({
        email: normalizedEmail,
      });
      if (result.type === "error") {
        setError("تعذّر إتمام الدفع. راجع بيانات الدفع ثم حاول مجدداً.");
      }
    } catch {
      setError("تعذّر إتمام الدفع. حاول مجدداً.");
    } finally {
      setConfirming(false);
    }
  }

  return (
    <>
      <Script
        src="https://js.stripe.com/dahlia/stripe.js"
        strategy="afterInteractive"
        onLoad={() => setStripeLoaded(true)}
        onError={() => setError("تعذّر تجهيز وسيلة الدفع. حاول مجدداً.")}
      />

      <section
        aria-labelledby="donation-checkout-heading"
        className="rounded-3xl border border-[var(--journal-border)] bg-white/90 p-5 shadow-[0_20px_60px_rgba(18,63,51,0.08)] sm:p-7"
      >
        <div className="flex items-start justify-between gap-4">
          <h2
            id="donation-checkout-heading"
            className="text-2xl font-bold text-[var(--journal-accent-strong)]"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            اختر مقدار المساهمة
          </h2>
          <span className="rounded-full border border-[var(--journal-border)] bg-[var(--journal-paper)] px-3 py-1 text-xs font-semibold text-slate-600">
            دفع آمن
          </span>
        </div>

        {config ? (
          <>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {config.preset_amounts_minor.map((amount) => (
                <button
                  key={amount}
                  type="button"
                  onClick={() => {
                    setCustomMode(false);
                    setSelectedAmount(amount);
                    setClientSecret(null);
                    setDisplayTotal(null);
                    setError(null);
                  }}
                  aria-pressed={!customMode && selectedAmount === amount}
                  className={`rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                    !customMode && selectedAmount === amount
                      ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white shadow-sm"
                      : "border-[var(--journal-border)] bg-[var(--journal-paper)] text-slate-700 hover:border-[var(--journal-accent)]"
                  }`}
                >
                  {formatDonationAmount(
                    amount,
                    config.currency,
                    config.minor_unit_divisor,
                  )}
                </button>
              ))}
              <button
                type="button"
                onClick={() => {
                  setCustomMode(true);
                  setClientSecret(null);
                  setDisplayTotal(null);
                  setError(null);
                }}
                aria-pressed={customMode}
                className={`rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                  customMode
                    ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white shadow-sm"
                    : "border-[var(--journal-border)] bg-[var(--journal-paper)] text-slate-700 hover:border-[var(--journal-accent)]"
                }`}
              >
                مبلغ آخر
              </button>
            </div>

            {customMode ? (
              <label className="mt-4 block text-sm font-medium text-slate-700">
                مقدار المساهمة ({config.currency.toUpperCase()})
                <input
                  inputMode="decimal"
                  value={customAmount}
                  onChange={(event) => {
                    setCustomAmount(event.target.value);
                    setClientSecret(null);
                    setDisplayTotal(null);
                  }}
                  placeholder="25.00"
                  className="mt-2 w-full rounded-xl border border-[var(--journal-border)] bg-white px-4 py-3 text-base outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[color:rgba(36,88,74,0.12)]"
                />
              </label>
            ) : null}

            <p className="mt-3 text-xs leading-6 text-slate-500">
              تُحدَّد المساهمة بهذه العملة أولاً، ثم تظهر لك العملة المحلية المتاحة تلقائياً عند تجهيز الدفع.
            </p>
          </>
        ) : null}

        {!clientSecret ? (
          <button
            type="button"
            onClick={startCheckout}
            disabled={!config || !amountIsValid || starting}
            className="mt-6 w-full rounded-xl bg-[var(--journal-accent)] px-5 py-3.5 text-base font-bold text-white shadow-sm transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {starting ? "جارٍ تجهيز الدفع…" : "متابعة إلى الدفع الآمن"}
          </button>
        ) : (
          <form onSubmit={submitPayment} className="mt-7 space-y-5">
            <div className="rounded-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)] p-4">
              <label className="block text-sm font-medium text-slate-700">
                البريد الإلكتروني
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setEmailSynced(false);
                    setEmailError(null);
                  }}
                  onBlur={() => {
                    void syncEmailToCheckout();
                  }}
                  aria-invalid={emailError ? "true" : undefined}
                  placeholder="name@example.com"
                  className="mt-2 w-full rounded-xl border border-[var(--journal-border)] bg-white px-4 py-3 text-left text-base outline-none transition focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[color:rgba(36,88,74,0.12)]"
                  dir="ltr"
                />
              </label>
              <p className="mt-2 text-xs leading-6 text-slate-500">
                البريد الإلكتروني مطلوب لإتمام الدفع، ونرسل إليه تأكيداً عربياً بعد ثبوت نجاح الدفع.
              </p>
              {emailError ? (
                <p role="alert" className="mt-2 text-xs font-medium text-red-700">
                  {emailError}
                </p>
              ) : null}
            </div>

            <div className="rounded-2xl border border-[var(--journal-border)] bg-white p-4 sm:p-5">
              <p className="mb-3 text-sm font-semibold text-slate-800">العملة ووسيلة الدفع</p>
              <div ref={currencySelectorHost} id="donation-currency-selector" dir="rtl" />
              <div className="mt-4" ref={paymentElementHost} id="donation-payment-element" dir="rtl" />
            </div>

            <div className="rounded-xl bg-[var(--journal-paper)] px-4 py-3 text-sm text-slate-700">
              <span className="font-semibold">المجموع:</span>{" "}
              {displayTotal ?? "جارٍ التحقق من المبلغ…"}
            </div>

            <button
              type="submit"
              disabled={
                !checkoutReady ||
                !canConfirm ||
                !displayTotal ||
                !emailSynced ||
                emailSyncing ||
                confirming
              }
              className="w-full rounded-xl bg-[var(--journal-accent)] px-5 py-3.5 text-base font-bold text-white shadow-sm transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {confirming
                ? "جارٍ إتمام الدفع…"
                : emailSyncing
                  ? "جارٍ التحقق من البريد الإلكتروني…"
                  : "ساهم في دعم البيان"}
            </button>
          </form>
        )}

        {error ? (
          <div
            role="alert"
            className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          >
            {error}
          </div>
        ) : null}

        <div className="mt-6 border-t border-[var(--journal-border)] pt-4 text-xs leading-6 text-slate-500">
          <p>
            تتم عملية الدفع عبر حقول آمنة ومشفّرة، ولا تستقبل خوادم مجلة البيان أرقام البطاقة أو رمز الأمان.
          </p>
        </div>
      </section>
    </>
  );
}
