"use client";

import { Check, ChevronDown } from "lucide-react";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import {
  MAPPING_FONTS,
  type EditableMappingFontId,
} from "@/lib/mapping-fonts";

import styles from "./mapping-font-selector.module.css";

function previewClassName(fontId: EditableMappingFontId): string | undefined {
  if (fontId === "takween") return styles.takween;
  if (fontId === "diwani") return styles.diwani;
  if (fontId === "diwaniOutline") return styles.diwaniOutline;
  if (fontId === "maghribi") return styles.maghribi;
  return undefined;
}

type PickerOption = {
  id: EditableMappingFontId;
  labelAr: string;
  descriptionAr: string;
};

const CUSTOM_OPTION: PickerOption = {
  id: "custom",
  labelAr: "تنسيق محفوظ سابقاً",
  descriptionAr: "صيغة قديمة أو مخصصة محفوظة كما هي.",
};

export function MappingFontSelector({
  id,
  value,
  onChange,
  ariaLabel,
}: {
  id: string;
  value: EditableMappingFontId;
  onChange: (value: EditableMappingFontId) => void;
  ariaLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const listboxId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const options = useMemo<PickerOption[]>(
    () => [
      ...(value === "custom" ? [CUSTOM_OPTION] : []),
      ...MAPPING_FONTS.map((font) => ({
        id: font.id,
        labelAr: font.labelAr,
        descriptionAr: font.descriptionAr,
      })),
    ],
    [value],
  );

  const selected =
    options.find((option) => option.id === value) ?? options[0] ?? CUSTOM_OPTION;
  const selectedIndex = Math.max(
    0,
    options.findIndex((option) => option.id === value),
  );
  const [activeIndex, setActiveIndex] = useState(selectedIndex);
  const selectedPreviewClass = previewClassName(value);

  useEffect(() => {
    if (!open) return;
    setActiveIndex(selectedIndex);
    requestAnimationFrame(() => optionRefs.current[selectedIndex]?.focus());
  }, [open, selectedIndex]);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }

    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  function choose(fontId: EditableMappingFontId) {
    onChange(fontId);
    setOpen(false);
    requestAnimationFrame(() => triggerRef.current?.focus());
  }

  function moveActive(next: number) {
    const bounded = (next + options.length) % options.length;
    setActiveIndex(bounded);
    optionRefs.current[bounded]?.focus();
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      const next =
        event.key === "ArrowDown"
          ? Math.min(selectedIndex + 1, options.length - 1)
          : Math.max(selectedIndex - 1, 0);
      setActiveIndex(next);
      requestAnimationFrame(() => optionRefs.current[next]?.focus());
    }
  }

  function handleOptionKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(index + 1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(index - 1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      moveActive(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      moveActive(options.length - 1);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    }
  }

  return (
    <div ref={rootRef} className="min-w-0">
      <button
        ref={triggerRef}
        id={id}
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleTriggerKeyDown}
        className="flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 text-start outline-none transition hover:border-[var(--journal-accent)] focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
      >
        <span className="min-w-0">
          <span className="block text-sm font-semibold text-slate-800">
            {selected.labelAr}
          </span>
          <span
            aria-hidden
            className={`mt-0.5 block truncate text-lg leading-7 text-slate-700 ${selectedPreviewClass ?? ""}`}
          >
            {value === "custom" ? "الصيغة المحفوظة" : "أبجد هوز"}
          </span>
        </span>
        <ChevronDown
          aria-hidden
          className={`h-4 w-4 shrink-0 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open ? (
        <div
          id={listboxId}
          role="listbox"
          aria-label={ariaLabel}
          className="mt-2 overflow-hidden rounded-xl border border-[var(--journal-border)] bg-white shadow-lg"
        >
          {options.map((option, index) => {
            const optionPreviewClass = previewClassName(option.id);
            const selectedOption = option.id === value;
            return (
              <button
                key={option.id}
                ref={(element) => {
                  optionRefs.current[index] = element;
                }}
                type="button"
                role="option"
                aria-selected={selectedOption}
                tabIndex={index === activeIndex ? 0 : -1}
                onFocus={() => setActiveIndex(index)}
                onKeyDown={(event) => handleOptionKeyDown(event, index)}
                onClick={() => choose(option.id)}
                className={`flex min-h-14 w-full items-center gap-3 border-b border-[var(--journal-border)] px-3 py-2.5 text-start transition last:border-b-0 hover:bg-[var(--journal-accent-soft)] focus:bg-[var(--journal-accent-soft)] focus:outline-none ${
                  selectedOption ? "bg-[var(--journal-accent-soft)]/70" : "bg-white"
                }`}
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-slate-800">
                    {option.labelAr}
                  </span>
                  <span
                    aria-hidden
                    className={`mt-0.5 block text-lg leading-7 text-slate-700 ${optionPreviewClass ?? ""}`}
                  >
                    {option.id === "custom" ? "الصيغة المحفوظة" : "أبجد هوز"}
                  </span>
                </span>
                {selectedOption ? (
                  <Check
                    aria-hidden
                    className="h-4 w-4 shrink-0 text-[var(--journal-accent-strong)]"
                  />
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}

      <p
        className={`mt-1.5 text-xs leading-5 ${
          value === "custom" ? "text-amber-700" : "text-slate-500"
        }`}
      >
        {selected.descriptionAr}
      </p>
    </div>
  );
}
