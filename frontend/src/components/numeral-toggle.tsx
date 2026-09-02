"use client";

import { useNumerals } from "@/components/numeral-provider";
import { numeralSample } from "@/lib/numerals";

export function NumeralToggle({ mobile = false }: { mobile?: boolean }) {
  const { numeralSystem, toggleNumeralSystem } = useNumerals();
  const usingWestern = numeralSystem === "latn";
  const actionLabel = usingWestern
    ? "استخدام الأرقام العربية المشرقية"
    : "استخدام الأرقام الغربية";

  return (
    <button
      type="button"
      aria-label={actionLabel}
      aria-pressed={usingWestern}
      onClick={toggleNumeralSystem}
      className={
        mobile
          ? "flex min-h-11 w-full items-center justify-between gap-3 px-4 text-sm font-medium text-slate-700 transition hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
          : "hidden min-h-10 min-w-10 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-2 text-sm font-bold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] md:inline-flex"
      }
    >
      {mobile ? <span>نظام الأرقام</span> : null}
      <span dir="ltr" aria-hidden>
        {numeralSample(numeralSystem)}
      </span>
      <span className="sr-only" aria-live="polite">
        {usingWestern ? "الأرقام الغربية مفعّلة" : "الأرقام العربية المشرقية مفعّلة"}
      </span>
    </button>
  );
}
