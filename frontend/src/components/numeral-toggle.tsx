"use client";

import { Hash } from "lucide-react";
import { useNumerals } from "@/components/numeral-provider";
import { numeralSample } from "@/lib/numerals";

export function NumeralToggle({ mobile = false }: { mobile?: boolean }) {
  const { numeralSystem, setNumeralSystem, toggleNumeralSystem } = useNumerals();
  const usingWestern = numeralSystem === "latn";
  const actionLabel = usingWestern
    ? "استخدام الأرقام العربية المشرقية"
    : "استخدام الأرقام الغربية";

  if (mobile) {
    const options = [
      { id: "arab" as const, label: "عربية مشرقية", sample: "١٢٣" },
      { id: "latn" as const, label: "عربية مغربية", sample: "123" },
    ];

    return (
      <section className="px-4 py-4" aria-labelledby="numeral-system-label">
        <div className="mb-3 flex items-start gap-2.5">
          <span
            className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[var(--journal-accent-soft)] text-[var(--journal-accent)]"
            aria-hidden
          >
            <Hash className="h-4 w-4" strokeWidth={2} />
          </span>
          <span>
            <span
              id="numeral-system-label"
              className="block text-sm font-bold text-slate-800"
            >
              شكل الأرقام
            </span>
            <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">
              اختر الشكل الذي تفضّله في جميع صفحات المجلة
            </span>
          </span>
        </div>

        <div
          role="radiogroup"
          aria-labelledby="numeral-system-label"
          className="grid grid-cols-2 gap-1 rounded-xl border border-[var(--journal-border)] bg-white p-1 shadow-sm"
        >
          {options.map((option) => {
            const selected = numeralSystem === option.id;
            return (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={selected}
                onClick={() => setNumeralSystem(option.id)}
                className={`relative flex min-h-16 flex-col items-center justify-center gap-0.5 rounded-lg px-2 text-center transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 ${
                  selected
                    ? "bg-[var(--journal-accent)] text-white shadow-sm"
                    : "text-slate-600 hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
                }`}
              >
                <span
                  dir="ltr"
                  className={`text-base font-bold ${selected ? "text-white" : "text-slate-800"}`}
                  aria-hidden
                >
                  {option.sample}
                </span>
                <span className="text-xs font-semibold leading-tight">
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      </section>
    );
  }

  return (
    <button
      type="button"
      aria-label={actionLabel}
      aria-pressed={usingWestern}
      onClick={toggleNumeralSystem}
      className="group hidden min-h-10 items-center gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-1.5 py-1 text-slate-700 shadow-sm transition duration-200 hover:border-[var(--journal-accent)] hover:bg-[var(--journal-accent-soft)]/45 hover:text-[var(--journal-accent-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--journal-accent)]/30 md:inline-flex"
    >
      <span
        dir="ltr"
        className="grid h-7 min-w-9 place-items-center rounded-md bg-[var(--journal-accent-soft)] px-1.5 text-sm font-bold text-[var(--journal-accent-strong)] transition group-hover:bg-white"
        aria-hidden
      >
        {numeralSample(numeralSystem)}
      </span>
      <span className="hidden pe-1 text-xs font-semibold leading-none lg:inline">
        {usingWestern ? "عربية مغربية" : "عربية مشرقية"}
      </span>
      <span className="sr-only" aria-live="polite">
        {usingWestern ? "الأرقام الغربية مفعّلة" : "الأرقام العربية المشرقية مفعّلة"}
      </span>
    </button>
  );
}
