"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useSignIn } from "@clerk/nextjs";
import { FormEvent, Suspense, useState } from "react";
import { EmailField } from "@/components/email-field";
import { PasswordField } from "@/components/password-field";
import { buttonClassName, cardClassName, translateClerkError } from "@/lib/auth-ui";

function safeNextPath(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) {
    return "/";
  }
  return raw;
}

function SignInForm() {
  const { signIn, fetchStatus } = useSignIn();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = safeNextPath(searchParams.get("next"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isReady = fetchStatus !== "fetching" && signIn;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!signIn) return;

    setLoading(true);
    setError(null);

    try {
      const { error: passwordError } = await signIn.password({
        identifier: email,
        password,
      });

      if (passwordError) {
        setError(translateClerkError(passwordError));
        return;
      }

      if (signIn.status !== "complete") {
        setError("يتطلّب تسجيل الدخول خطوة إضافية غير مدعومة حالياً.");
        return;
      }

      const { error: finalizeError } = await signIn.finalize({
        navigate: async () => {
          router.push(nextPath);
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
            تسجيل الدخول
          </h1>
          <p className="mt-2 text-sm text-slate-600">أدخل بريدك وكلمة المرور للوصول إلى حسابك.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
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
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={1}
            />

            {error ? (
              <p className="text-sm text-red-700" role="alert">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              className={buttonClassName}
              disabled={!isReady || loading}
            >
              {loading ? "جارٍ الدخول..." : "دخول"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            ليس لديك حساب؟{" "}
            <Link
              href="/tasjil"
              className="font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
            >
              إنشاء حساب
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
          جارٍ التحميل...
        </div>
      }
    >
      <SignInForm />
    </Suspense>
  );
}
