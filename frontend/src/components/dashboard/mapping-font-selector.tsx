"use client";

import { Check, ChevronDown } from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import {
  MAPPING_FONTS,
  mappingFontLabel,
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
  const listboxId = `${id}-listbox`;
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [open, setOpen] = useState(false);

  const optionIds = useMemo<EditableMappingFontId[]>(
    () => [
      ...(value === "custom" ? (["custom"] as const) : []),
      ...MAPPING_FONTS.map((font) => font.id),
    ],
    [value],
  );
  const selected = MAPPING_FONTS.find((font) => font.id === value);
  const selectedPreviewClass = previewClassName(value);
  const selectedIndex = Math.max(0, optionIds.indexOf(value));
  const [activeIndex, setActiveIndex] = useState(selectedIndex);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }

    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setActiveIndex(selectedIndex);
  }, [open, selectedIndex]);

  useEffect(() => {
    if (!open) return;
    optionRefs.current[activeIndex]?.focus();
  }, [activeIndex, open]);

  function closeAndRestoreFocus() {
    setOpen(false);
    requestAnimationFrame(() => triggerRef.current?.focus());
  }

  function choose(fontId: EditableMappingFontId) {
    onChange(fontId);
    closeAndRestoreFocus();
  }

  function moveActive(nextIndex: number) {
    const length = optionIds.length;
    if (length === 0) return;
    setActiveIndex((nextIndex + length) % length);
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex(
        event.key === "ArrowDown"
          ? selectedIndex
          : Math.max(0, selectedIndex - 1),
      );
    }
  }

  function handleOptionKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(index - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      moveActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      moveActive(optionIds.length - 1);
    } else if (event.key === "Escape") {
      event.preventDefault();
      closeAndRestoreFocus();
    } else if (event.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div ref={rootRef} className="relative min-w-0">
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
          <span
            className={`block truncate text-sm font-semibold text-slate-800 ${selectedPreviewClass ?? ""}`}
          >
            {mappingFontLabel(value)}
          </span>
          {selected ? (
            <span className="mt-0.5 block truncate text-xs font-normal text-slate-500">
              {selected.descriptionAr}
            </span>
          ) : null}
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
          className="absolute inset-x-0 top-full z-30 mt-1.5 max-h-80 overflow-y-auto rounded-xl border border-[var(--journal-border)] bg-white p-1.5 shadow-xl"
        >
          {optionIds.map((fontId, index) => {
            const font = MAPPING_FONTS.find((candidate) => candidate.id === fontId);
            const isCustom = fontId === "custom";
            const isRaw = fontId === "none";
            const optionPreviewClass = previewClassName(fontId);
            const label = isCustom ? "تنسيق مخصص محفوظ" : font?.labelAr ?? fontId;
            const description = isCustom
              ? "صيغة قديمة أو مخصصة محفوظة كما هي."
              : font?.descriptionAr;

            return (
              <button
                key={fontId}
                ref={(node) => {
                  optionRefs.current[index] = node;
                }}
                type="button"
                role="option"
                aria-selected={value === fontId}
                tabIndex={activeIndex === index ? 0 : -1}
                onClick={() => choose(fontId)}
                onKeyDown={(event) => handleOptionKeyDown(event, index)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-start outline-none transition hover:bg-[var(--journal-accent-soft)] focus:bg-[var(--journal-accent-soft)] focus:ring-2 focus:ring-inset focus:ring-[var(--journal-accent)] ${
                  isRaw ? "mt-1.5 border-t border-[var(--journal-border)] pt-3.5" : ""
                }`}
              >
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800">{label}</span>
                    {isRaw ? (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                        متقدم
                      </span>
                    ) : null}
                  </span>
                  {description ? (
                    <span className="mt-0.5 block text-xs leading-5 text-slate-500">
                      {description}
                    </span>
                  ) : null}
                </span>

                {!isCustom && !isRaw ? (
                  <span
                    aria-hidden
                    className={`shrink-0 rounded-md border border-[var(--journal-border)] bg-white px-2 py-1 text-lg leading-none text-slate-800 ${optionPreviewClass ?? ""}`}
                  >
                    أبجد هوز
                  </span>
                ) : null}

                <span className="grid h-5 w-5 shrink-0 place-items-center text-[var(--journal-accent-strong)]">
                  {value === fontId ? <Check aria-hidden className="h-4 w-4" /> : null}
                </span>
              </button>
            );
          })}
        </div>
      ) : null}

      {value === "custom" ? (
        <p className="mt-1.5 text-xs leading-5 text-amber-700">
          ستبقى هذه الصيغة محفوظة كما هي ما لم تغيّر القيمة أو الخط.
        </p>
      ) : null}
    </div>
  );
}
