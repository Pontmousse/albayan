"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignIn } from "@clerk/nextjs";
import { FormEvent, useState } from "react";
import { EmailField } from "@/components/email-field";
import { EmailCodeForm } from "@/components/email-code-form";
import { PasswordField } from "@/components/password-field";
import {
  buttonClassName,
  cardClassName,
  PASSWORD_MIN_LENGTH_HINT,
  translateClerkError,
} from "@/lib/auth-ui";

type RecoveryStep = "email" | "code" | "password";

export default function PasswordRecoveryPage() {
  const { signIn, fetchStatus } = useSignIn();
  const router = useRouter();
  const [step, setStep] = useState<RecoveryStep>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const isReady = fetchStatus !== "fetching" && signIn;

  async function sendResetCode() {
    if (!signIn) return;

    const identifier = email.trim().toLowerCase();
    if (!identifier) {
      setError("يرجى إدخال البريد الإلكتروني.");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      await signIn.create({ identifier });
      const { error: sendError } = await signIn.resetPasswordEmailCode.sendCode();
      if (sendError) {
        setError(translateClerkError(sendError));
        return;
      }
      setStep("code");
      setMessage("أرسلنا رمز استعادة كلمة المرور إلى بريدك.");
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendResetCode();
  }

  async function handleVerifyCode() {
    if (!signIn) return;

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const { error: verifyError } =
        await signIn.resetPasswordEmailCode.verifyCode({ code });
      if (verifyError) {
        setError(translateClerkError(verifyError));
        return;
      }
      setStep("password");
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleResendCode() {
    if (!signIn) return;

    setResendLoading(true);
    setError(null);

    try {
      const { error: sendError } = await signIn.resetPasswordEmailCode.sendCode();
      if (sendError) {
        setError(translateClerkError(sendError));
      } else {
        setMessage("أُعيد إرسال رمز الاستعادة إلى بريدك.");
      }
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setResendLoading(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!signIn) return;

    if (password !== confirmPassword) {
      setError("كلمة المرور وتأكيدها غير متطابقين.");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const { error: passwordError } =
        await signIn.resetPasswordEmailCode.submitPassword({
          password,
          signOutOfOtherSessions: true,
        });
      if (passwordError) {
        setError(translateClerkError(passwordError));
        return;
      }

      if (signIn.status !== "complete") {
        setError("تم تغيير كلمة المرور، لكن تسجيل الدخول يتطلب خطوة إضافية.");
        return;
      }

      const { error: finalizeError } = await signIn.finalize({
        navigate: async () => {
          router.push("/");
        },
      });
      if (finalizeError) {
        setError(translateClerkError(finalizeError));
      }
    } catch (err) {
      setError(translateClerkError(err));
    } finally {
      setLoading(false);
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
            استعادة كلمة المرور
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            أدخل بريدك، ثم استخدم رمز التحقق الذي ترسله Clerk عبر بريد البيان
            الموحّد.
          </p>

          {step === "email" ? (
            <form onSubmit={handleEmailSubmit} className="mt-6 space-y-4" noValidate>
              <EmailField
                id="email"
                label="البريد الإلكتروني"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
              {error ? (
                <p className="text-sm text-red-700" role="alert">
                  {error}
                </p>
              ) : null}
              <button
                type="submit"
                className={`${buttonClassName} w-full`}
                disabled={!isReady || loading}
              >
                {loading ? "جارٍ الإرسال…" : "إرسال رمز الاستعادة"}
              </button>
            </form>
          ) : null}

          {step === "code" ? (
            <EmailCodeForm
              title="أدخل رمز الاستعادة"
              description="أرسلنا رمزاً إلى بريدك. أدخله هنا ثم اختر كلمة مرور جديدة."
              code={code}
              onCodeChange={setCode}
              onSubmit={handleVerifyCode}
              onResend={handleResendCode}
              loading={loading}
              resendLoading={resendLoading}
              error={error}
            />
          ) : null}

          {step === "password" ? (
            <form onSubmit={handlePasswordSubmit} className="mt-6 space-y-4" noValidate>
              <PasswordField
                id="password"
                label="كلمة المرور الجديدة"
                autoComplete="new-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                hint={PASSWORD_MIN_LENGTH_HINT}
              />
              <PasswordField
                id="confirmPassword"
                label="تأكيد كلمة المرور الجديدة"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
              {error ? (
                <p className="text-sm text-red-700" role="alert">
                  {error}
                </p>
              ) : null}
              <button
                type="submit"
                className={`${buttonClassName} w-full`}
                disabled={!isReady || loading}
              >
                {loading ? "جارٍ التحديث…" : "تحديث كلمة المرور"}
              </button>
            </form>
          ) : null}

          {message ? (
            <p className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              {message}
            </p>
          ) : null}

          <p className="mt-6 text-center text-sm text-slate-600">
            تذكرت كلمة المرور؟{" "}
            <Link
              href="/tawajjuh"
              className="font-semibold text-[var(--journal-accent)] hover:underline"
            >
              سجّل دخولك
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
