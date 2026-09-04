"use client";

import { useAuth, useReverification } from "@clerk/nextjs";
import { isReverificationCancelledError } from "@clerk/nextjs/errors";
import { FormEvent, useState } from "react";
import {
  API_BASE,
  arabicApiErrorMessage,
  type AccountDeletionRequestRead,
} from "@/lib/api";
import { buttonClassName, cardClassName } from "@/lib/auth-ui";

function parseError(data: Record<string, unknown>): string {
  return arabicApiErrorMessage(data, "تعذّر إرسال طلب حذف الحساب.");
}

export function AccountDeletionRequestCard() {
  const { getToken } = useAuth();
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submitDeletionRequest = useReverification(
    async (): Promise<AccountDeletionRequestRead | Record<string, unknown>> => {
      const token = await getToken({ skipCache: true });
      const response = await fetch(`${API_BASE}/api/v1/users/me/deletion-request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ reason: reason.trim() || null }),
      });

      const data = (await response.json()) as
        | AccountDeletionRequestRead
        | Record<string, unknown>;
      if (!response.ok && "clerk_error" in data) {
        return data;
      }
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      return data;
    },
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const request = await submitDeletionRequest();
      if ("id" in request) {
        setMessage("وصل طلب حذف الحساب إلى الإدارة للمراجعة.");
        setReason("");
      }
    } catch (err) {
      if (isReverificationCancelledError(err)) {
        setError("أُلغي التحقق الأمني، ولم يُرسل طلب حذف الحساب.");
      } else {
        setError(err instanceof Error ? err.message : "تعذّر إرسال الطلب.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className={`${cardClassName} border-red-200 bg-red-50/40 lg:col-span-2`}>
      <h2 className="text-lg font-bold text-red-800">منطقة حساسة</h2>
      <p className="mt-2 text-sm leading-6 text-red-900/80">
        حذف الحساب في مجلة علمية يحتاج مراجعة إدارية حتى لا تتضرر سجلات النشر
        والتحكيم. أرسل طلباً، وستراجعه الإدارة دون حذف حسابك تلقائياً.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label htmlFor="deletion-reason" className="block text-sm font-medium text-red-950">
          سبب الطلب أو ملاحظاتك، اختياري
        </label>
        <textarea
          id="deletion-reason"
          rows={4}
          maxLength={2000}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          className="w-full rounded-md border border-red-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-red-500 focus:ring-1 focus:ring-red-500"
        />

        {message ? (
          <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            {message}
          </p>
        ) : null}
        {error ? (
          <p className="rounded-md border border-red-300 bg-white px-3 py-2 text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}

        <button type="submit" disabled={loading} className={buttonClassName}>
          {loading ? "جارٍ التحقق والإرسال…" : "طلب حذف الحساب"}
        </button>
      </form>
    </section>
  );
}
