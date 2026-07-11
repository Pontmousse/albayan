"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "@/lib/api";
import { buttonClassName, cardClassName } from "@/lib/auth-ui";

type AcceptResponse = {
  id: string;
  article_id: string;
  role: "reviewer" | "editor";
  email: string;
  status: string;
};

const ROLE_LABELS = {
  reviewer: "مراجع",
  editor: "محرر",
} as const;

export default function DaawaPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const router = useRouter();
  const [result, setResult] = useState<AcceptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      const returnTo = encodeURIComponent(`/daawa/${token}`);
      router.replace(`/tawajjuh?next=${returnTo}`);
    }
  }, [isLoaded, isSignedIn, router, token]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !token) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    apiFetch<AcceptResponse>(`/api/v1/invitations/${token}/accept`, getToken, {
      method: "POST",
    })
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : "تعذّر قبول الدعوة.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [getToken, isLoaded, isSignedIn, token]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="mx-auto flex w-full max-w-lg flex-1 items-center justify-center px-6 py-16">
        <p className="text-sm text-slate-500">جارٍ التحقق من الجلسة...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center px-6 py-16">
      <div className={cardClassName}>
        <h1
          className="text-2xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          قبول الدعوة
        </h1>

        {loading ? (
          <p className="mt-4 text-sm text-slate-600">جارٍ قبول الدعوة...</p>
        ) : null}

        {error ? (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-red-700">{error}</p>
            <Link href="/" className={buttonClassName}>
              العودة للرئيسية
            </Link>
          </div>
        ) : null}

        {result ? (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-slate-700">
              تم قبول الدعوة بنجاح. دورك على المقال:{" "}
              <strong>{ROLE_LABELS[result.role]}</strong>.
            </p>
            <Link
              href={
                result.role === "reviewer"
                  ? "/maktabi/murajaati"
                  : result.role === "editor"
                    ? "/maktabi/tahriri"
                    : "/maktabi"
              }
              className={buttonClassName}
            >
              {result.role === "reviewer"
                ? "الانتقال إلى مراجعاتي"
                : result.role === "editor"
                  ? "الانتقال إلى تحريري"
                  : "الانتقال إلى مكتبي"}
            </Link>
          </div>
        ) : null}
      </div>
    </main>
  );
}
