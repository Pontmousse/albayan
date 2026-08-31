"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useSignUp } from "@clerk/nextjs";
import { FormEvent, Suspense, useState } from "react";
import { EmailField } from "@/components/email-field";
import { EmailCodeForm } from "@/components/email-code-form";
import { PasswordField } from "@/components/password-field";
import {
  buttonClassName,
  cardClassName,
  inputClassName,
  PASSWORD_MIN_LENGTH_HINT,
  translateClerkError,
} from "@/lib/auth-ui";

function SignUpForm() {
  const { signUp, fetchStatus } = useSignUp();
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationTicket = searchParams.get("__clerk_ticket");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [step, setStep] = useState<"details" | "verify-email">("details");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const isReady = fetchStatus !== "fetching" && signUp;
  const isInvitation = Boolean(invitationTicket);

  async function finalizeIfComplete(): Promise<boolean> {
    if (!signUp || signUp.status !== "complete") {
      return false;
    }

    const { error: finalizeError } = await signUp.finalize({
      navigate: async () => {
        router.push("/");
      },
    });

    if (finalizeError) {
      setError(translateClerkError(finalizeError));
      return false;
    }
    return true;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!signUp) return;

    if (password !== confirmPassword) {
      setError("كلمة المرور وتأكيدها غير متطابقين.");
      return;
    }

    setLoading(true);
    setError(null);

    const nameParts = fullName.trim().split(/\s+/);
    const firstName = nameParts[0] ?? "";
    const lastName = nameParts.slice(1).join(" ");

    try {
      if (invitationTicket) {
        const { error: ticketError } = await signUp.ticket({
          ticket: invitationTicket,
          firstName,
          lastName,
        });

        if (ticketError) {
          setError(translateClerkError(ticketError));
          return;
        }

        if (await finalizeIfComplete()) return;

        const { error: passwordError } = await signUp.password({ password });
        if (passwordError) {
          setError(translateClerkError(passwordError));
          return;
        }

        if (await finalizeIfComplete()) return;

        if (signUp.unverifiedFields.includes("email_address")) {
          const { error: verifyError } = await signUp.verifications.sendEmailCode();
          if (verifyError) {
            setError(translateClerkError(verifyError));
            return;
          }
          setStep("verify-email");
          return;
        }

        setError("قُبلت الدعوة، لكن التسجيل يتطلب خطوة إضافية غير مكتملة بعد.");
        return;
      }

      const { error: signUpError } = await signUp.password({
        emailAddress: email,
        password,
        firstName,
        lastName,
      });

      if (signUpError) {
        setError(translateClerkError(signUpError));
        return;
      }

      if (await finalizeIfComplete()) return;

      if (signUp.unverifiedFields.includes("email_address")) {
        const { error: verifyError } = await signUp.verifications.sendEmailCode();
        if (verifyError) {
          setError(translateClerkError(verifyError));
          return;
        }
        setStep("verify-email");
        return;
      }

      setError("يتطلّب التسجيل خطوة إضافية غير مكتملة بعد.");
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyEmailCode() {
    if (!signUp) return;

    setLoading(true);
    setError(null);

    try {
      const { error: verifyError } = await signUp.verifications.verifyEmailCode({
        code: emailCode,
      });

      if (verifyError) {
        setError(translateClerkError(verifyError));
        return;
      }

      if (await finalizeIfComplete()) return;
      setError("تم التحقق من البريد، لكن التسجيل يتطلب خطوة إضافية غير مكتملة بعد.");
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleResendEmailCode() {
    if (!signUp) return;

    setResendLoading(true);
    setError(null);

    try {
      const { error: verifyError } = await signUp.verifications.sendEmailCode();
      if (verifyError) {
        setError(translateClerkError(verifyError));
      }
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-10 sm:px-6">
        <div className={cardClassName}>
          <h1
            className="text-2xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {isInvitation ? "قبول الدعوة" : "إنشاء حساب"}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            {isInvitation
              ? "أكمل بياناتك لقبول الدعوة وإنشاء حسابك في مجلة البيان."
              : "انضم إلى مجلة البيان لإدارة ملفك الشخصي."}
          </p>

          {step === "verify-email" ? (
            <EmailCodeForm
              title="تحقق من بريدك الإلكتروني"
              description="أرسلنا رمز تحقق إلى بريدك. أدخل الرمز هنا لإكمال إنشاء الحساب."
              code={emailCode}
              onCodeChange={setEmailCode}
              onSubmit={handleVerifyEmailCode}
              onResend={handleResendEmailCode}
              loading={loading}
              resendLoading={resendLoading}
              error={error}
            />
          ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <div>
              <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">
                الاسم الكامل
              </label>
              <input
                id="fullName"
                type="text"
                autoComplete="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className={inputClassName}
                onInvalid={(e) => {
                  if (e.currentTarget.validity.valueMissing) {
                    e.currentTarget.setCustomValidity("يرجى إدخال الاسم الكامل.");
                  }
                }}
                onInput={(e) => e.currentTarget.setCustomValidity("")}
              />
            </div>
            {!isInvitation ? (
              <EmailField
                id="email"
                label="البريد الإلكتروني"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            ) : null}
            <PasswordField
              id="password"
              label="كلمة المرور"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              hint={PASSWORD_MIN_LENGTH_HINT}
            />
            <PasswordField
              id="confirmPassword"
              label="تأكيد كلمة المرور"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />

            <div id="clerk-captcha" />

            {error && (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading || !isReady} className={`${buttonClassName} w-full`}>
              {loading
                ? isInvitation
                  ? "جارٍ قبول الدعوة…"
                  : "جارٍ الإنشاء…"
                : isInvitation
                  ? "قبول الدعوة وإنشاء الحساب"
                  : "إنشاء حساب"}
            </button>
          </form>
          )}

          <p className="mt-6 text-center text-sm text-slate-600">
            لديك حساب؟{" "}
            <Link href="/tawajjuh" className="font-semibold text-[var(--journal-accent)] hover:underline">
              سجّل دخولك
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

export default function SignUpPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
          جارٍ التحميل...
        </div>
      }
    >
      <SignUpForm />
    </Suspense>
  );
}
