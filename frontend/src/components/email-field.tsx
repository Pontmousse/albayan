"use client";

import { InputHTMLAttributes } from "react";
import { inputClassName, setArabicFieldValidity } from "@/lib/auth-ui";

type EmailFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  id: string;
  label: string;
};

export function EmailField({ id, label, className, onInvalid, onInput, ...props }: EmailFieldProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        type="email"
        className={className ?? inputClassName}
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
    </div>
  );
}
