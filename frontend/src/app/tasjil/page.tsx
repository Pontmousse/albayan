"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignUp } from "@clerk/nextjs";
import { FormEvent, useState } from "react";
import { SimplePageFooter } from "@/components/simple-page-footer";
import { EmailField } from "@/components/email-field";
import { PasswordField } from "@/components/password-field";
import {
  buttonClassName,
  cardClassName,
  inputClassName,
  PASSWORD_MIN_LENGTH_HINT,
  translateClerkError,
} from "@/lib/auth-ui";

export default function SignUpPage() {
  const { signUp, fetchStatus } = useSignUp();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isReady = fetchStatus !== "fetching" && signUp;

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

      if (signUp.status === "complete") {
        const { error: finalizeError } = await signUp.finalize({
          navigate: async () => {
            router.push("/");
          },
        });

        if (finalizeError) {
          setError(translateClerkError(finalizeError));
        }
        return;
      }

      if (signUp.unverifiedFields.includes("email_address")) {
        const { error: verifyError } = await signUp.verifications.sendEmailCode();
        if (verifyError) {
          setError(translateClerkError(verifyError));
          return;
        }
        setError("تم إرسال رمز التحقق إلى بريدك. أكمل التحقق ثم سجّل الدخول.");
        return;
      }

      setError("يتطلّب التسجيل خطوة إضافية غير مكتملة بعد.");
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
            إنشاء حساب
          </h1>
          <p className="mt-2 text-sm text-slate-600">انضم إلى مجلة البيان لإدارة ملفك الشخصي.</p>

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
            <EmailField
              id="email"
              label="البريد الإلكتروني"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
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

            {error && (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading || !isReady} className={`${buttonClassName} w-full`}>
              {loading ? "جارٍ الإنشاء…" : "إنشاء حساب"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            لديك حساب؟{" "}
            <Link href="/tawajjuh" className="font-semibold text-[var(--journal-accent)] hover:underline">
              سجّل دخولك
            </Link>
          </p>
        </div>
      </main>
      <SimplePageFooter />
    </div>
  );
}
