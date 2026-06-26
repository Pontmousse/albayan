"use client";

import { InputHTMLAttributes, useState } from "react";
import { passwordInputClassName, setArabicFieldValidity } from "@/lib/auth-ui";

type PasswordFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  id: string;
  label: string;
  hint?: string;
};

export function PasswordField({
  id,
  label,
  hint,
  className,
  onInvalid,
  onInput,
  minLength = 8,
  ...props
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          minLength={minLength}
          className={className ?? passwordInputClassName}
          onInvalid={(event) => {
            setArabicFieldValidity(event.currentTarget);
            onInvalid?.(event);
          }}
          onInput={(event) => {
            event.currentTarget.setCustomValidity("");
            onInput?.(event);
          }}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          className="absolute end-2 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs font-medium text-[var(--journal-accent)] hover:bg-[var(--journal-accent-soft)]"
          aria-label={visible ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"}
          aria-pressed={visible}
        >
          {visible ? "إخفاء" : "إظهار"}
        </button>
      </div>
      {hint && <p className="mt-1 text-xs leading-5 text-slate-500">{hint}</p>}
    </div>
  );
}
