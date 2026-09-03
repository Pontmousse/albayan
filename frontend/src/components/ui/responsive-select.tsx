"use client";

import { Check, ChevronDown } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { MobileSheet } from "@/components/mobile-sheet";

export type ResponsiveSelectOption<T extends string> = {
  value: T;
  label: string;
  description?: string;
};

type OpenMode = "desktop" | "mobile" | null;

export function ResponsiveSelect<T extends string>({
  label,
  value,
  options,
  onChange,
  disabled = false,
}: {
  label: string;
  value: T;
  options: readonly ResponsiveSelectOption<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
}) {
  const labelId = useId();
  const listId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const initialOptionRef = useRef<HTMLElement | null>(null);
  const [openMode, setOpenMode] = useState<OpenMode>(null);
  const selectedIndex = Math.max(
    0,
    options.findIndex((option) => option.value === value),
  );
  const [activeIndex, setActiveIndex] = useState(selectedIndex);
  const open = openMode !== null;
  const selected = options[selectedIndex] ?? options[0];

  const close = useCallback((restoreFocus = true) => {
    setOpenMode(null);
    if (restoreFocus) {
      requestAnimationFrame(() => triggerRef.current?.focus());
    }
  }, []);

  const show = useCallback(
    (index = selectedIndex) => {
      if (disabled || options.length === 0) return;
      setActiveIndex(index);
      setOpenMode(
        window.matchMedia("(min-width: 768px)").matches
          ? "desktop"
          : "mobile",
      );
    },
    [disabled, options.length, selectedIndex],
  );

  useEffect(() => {
    if (openMode !== "desktop") return;
    const frame = requestAnimationFrame(() => {
      optionRefs.current[activeIndex]?.focus();
    });
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) close(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [activeIndex, close, openMode]);

  useEffect(() => {
    if (!openMode) return;
    function onViewportChange() {
      close(false);
    }
    const media = window.matchMedia("(min-width: 768px)");
    media.addEventListener("change", onViewportChange);
    return () => media.removeEventListener("change", onViewportChange);
  }, [close, openMode]);

  function focusOption(index: number) {
    const next = (index + options.length) % options.length;
    setActiveIndex(next);
    optionRefs.current[next]?.focus();
  }

  function choose(index: number) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    close();
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      show(selectedIndex);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      show(options.length - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      show(0);
    } else if (event.key === "End") {
      event.preventDefault();
      show(options.length - 1);
    }
  }

  function handleOptionKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusOption(index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      focusOption(index - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      focusOption(0);
    } else if (event.key === "End") {
      event.preventDefault();
      focusOption(options.length - 1);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    } else if (event.key === "Tab") {
      close(false);
    }
  }

  const optionItems = (mobile: boolean) =>
    options.map((option, index) => {
      const isSelected = option.value === value;
      const listOpen = mobile
        ? openMode === "mobile"
        : openMode === "desktop";
      return (
        <li key={option.value} role="none">
          <button
            ref={(element) => {
              const ownsRefs =
                (mobile && openMode === "mobile") ||
                (!mobile && openMode !== "mobile");
              if (ownsRefs) optionRefs.current[index] = element;
              if (ownsRefs && index === activeIndex) {
                initialOptionRef.current = element;
              }
            }}
            type="button"
            role="option"
            aria-selected={isSelected}
            tabIndex={listOpen && index === activeIndex ? 0 : -1}
            onClick={() => choose(index)}
            onKeyDown={(event) => handleOptionKeyDown(event, index)}
            className={`flex min-h-11 w-full items-center gap-3 px-3.5 py-2.5 text-start transition-colors duration-150 ${
              isSelected
                ? "bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
                : "text-slate-800 hover:bg-[var(--journal-accent-soft)]"
            }`}
          >
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">{option.label}</span>
              {option.description ? (
                <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">
                  {option.description}
                </span>
              ) : null}
            </span>
            <Check
              aria-hidden
              className={`h-4 w-4 shrink-0 ${isSelected ? "opacity-100" : "opacity-0"}`}
            />
          </button>
        </li>
      );
    });

  return (
    <div ref={rootRef} className="relative min-w-0">
      <span
        id={labelId}
        className="mb-1.5 block text-xs font-semibold text-slate-700"
      >
        {label}
      </span>
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-labelledby={labelId}
        aria-controls={open ? listId : undefined}
        aria-expanded={open}
        aria-haspopup="listbox"
        disabled={disabled}
        onClick={() => (open ? close() : show())}
        onKeyDown={handleTriggerKeyDown}
        className={`flex min-h-11 w-full items-center justify-between gap-3 rounded-md border bg-white px-3 text-start text-sm outline-none transition disabled:cursor-wait disabled:opacity-70 ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)]/35 text-[var(--journal-accent-strong)] ring-2 ring-[var(--journal-accent-soft)]"
            : "border-[var(--journal-border)] text-slate-900 hover:border-[var(--journal-accent)] focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
        }`}
      >
        <span className="min-w-0 truncate">{selected?.label}</span>
        <ChevronDown
          aria-hidden
          className={`h-4 w-4 shrink-0 text-slate-500 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      <div
        aria-hidden={openMode !== "desktop"}
        className={`dropdown-panel absolute start-0 top-full z-50 mt-1.5 hidden w-full min-w-[12rem] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md md:block ${
          openMode === "desktop"
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        <ul
          id={openMode === "desktop" ? listId : undefined}
          role="listbox"
          aria-labelledby={labelId}
          className="py-1"
        >
          {optionItems(false)}
        </ul>
      </div>

      <MobileSheet
        open={openMode === "mobile"}
        onClose={() => close()}
        title={label}
        initialFocusRef={initialOptionRef}
      >
        <ul
          id={openMode === "mobile" ? listId : undefined}
          role="listbox"
          aria-labelledby={labelId}
          className="py-1"
        >
          {optionItems(true)}
        </ul>
      </MobileSheet>
    </div>
  );
}
