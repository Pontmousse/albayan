"use client";

import { FormEvent } from "react";
import { useNumerals } from "@/components/numeral-provider";
import { buttonClassName, inputClassName } from "@/lib/auth-ui";
import { normalizeNumericInput } from "@/lib/numerals";

type EmailCodeFormProps = {
  title: string;
  description: string;
  code: string;
  onCodeChange: (value: string) => void;
  onSubmit: () => void | Promise<void>;
  onResend?: () => void | Promise<void>;
  submitLabel?: string;
  resendLabel?: string;
  loading?: boolean;
  resendLoading?: boolean;
  error?: string | null;
  codeLength?: number;
};

export function EmailCodeForm({
  title,
  description,
  code,
  onCodeChange,
  onSubmit,
  onResend,
  submitLabel = "تحقق من الرمز",
  resendLabel = "إعادة إرسال الرمز",
  loading = false,
  resendLoading = false,
  error = null,
  codeLength,
}: EmailCodeFormProps) {
  const { formatDigits } = useNumerals();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
      <div>
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        <p className="mt-1.5 text-sm leading-6 text-slate-600">{description}</p>
      </div>

      <div>
        <label htmlFor="email-code" className="mb-1 block text-sm font-medium text-slate-700">
          رمز التحقق
        </label>
        <input
          id="email-code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          required
          minLength={codeLength}
          maxLength={codeLength}
          dir="ltr"
          value={formatDigits(code)}
          onChange={(event) => {
            const normalized = normalizeNumericInput(event.target.value, codeLength);
            if (normalized !== null) onCodeChange(normalized);
          }}
          className={`${inputClassName} text-center font-mono text-lg tracking-[0.35em]`}
        />
      </div>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}

      <button type="submit" disabled={loading} className={`${buttonClassName} w-full`}>
        {loading ? "جارٍ التحقق…" : submitLabel}
      </button>

      {onResend ? (
        <button
          type="button"
          onClick={() => void onResend()}
          disabled={loading || resendLoading}
          className="w-full rounded-md px-4 py-2 text-sm font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline disabled:opacity-60"
        >
          {resendLoading ? "جارٍ الإرسال…" : resendLabel}
        </button>
      ) : null}
    </form>
  );
}
