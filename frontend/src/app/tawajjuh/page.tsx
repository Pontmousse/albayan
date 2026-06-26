"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignIn } from "@clerk/nextjs";
import { FormEvent, useState } from "react";
import { EmailField } from "@/components/email-field";
import { PasswordField } from "@/components/password-field";
import { buttonClassName, cardClassName, translateClerkError } from "@/lib/auth-ui";

export default function SignInPage() {
  const { signIn, fetchStatus } = useSignIn();
  const router = useRouter();
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

            {error && (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading || !isReady} className={`${buttonClassName} w-full`}>
              {loading ? "جارٍ الدخول…" : "تسجيل الدخول"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            ليس لديك حساب؟{" "}
            <Link href="/tasjil" className="font-semibold text-[var(--journal-accent)] hover:underline">
              سجّل الآن
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
