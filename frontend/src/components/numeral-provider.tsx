"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  DEFAULT_NUMERAL_SYSTEM,
  NUMERAL_STORAGE_KEY,
  formatDigits as formatDigitsValue,
  formatNumber as formatNumberValue,
  isNumeralSystem,
  type NumeralSystem,
} from "@/lib/numerals";
import {
  formatDate as formatDateValue,
  formatDateTime as formatDateTimeValue,
  formatHijriYear as formatHijriYearValue,
  formatRelativeTime as formatRelativeTimeValue,
} from "@/lib/format-date";

const NUMERAL_CHANGE_EVENT = "albayan:numeral-system-change";

function getBrowserSnapshot(): NumeralSystem {
  try {
    const stored = window.localStorage.getItem(NUMERAL_STORAGE_KEY);
    if (isNumeralSystem(stored)) return stored;
  } catch {
    // قد يُحجب localStorage في بعض أوضاع الخصوصية؛ نرجع للقيمة على الجذر.
  }
  const initialized = document.documentElement.dataset.numeralSystem;
  return isNumeralSystem(initialized) ? initialized : DEFAULT_NUMERAL_SYSTEM;
}

function subscribe(onStoreChange: () => void): () => void {
  function onStorage(event: StorageEvent) {
    if (event.key === NUMERAL_STORAGE_KEY) onStoreChange();
  }
  window.addEventListener("storage", onStorage);
  window.addEventListener(NUMERAL_CHANGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(NUMERAL_CHANGE_EVENT, onStoreChange);
  };
}

function saveNumeralSystem(system: NumeralSystem) {
  try {
    window.localStorage.setItem(NUMERAL_STORAGE_KEY, system);
  } catch {
    // يبقى الخيار فعالًا للجلسة الحالية حتى إن منع المتصفح التخزين الدائم.
  }
  document.documentElement.dataset.numeralSystem = system;
  window.dispatchEvent(new Event(NUMERAL_CHANGE_EVENT));
}

type NumeralContextValue = {
  numeralSystem: NumeralSystem;
  setNumeralSystem: (system: NumeralSystem) => void;
  toggleNumeralSystem: () => void;
  formatNumber: (value: number | bigint, options?: Intl.NumberFormatOptions) => string;
  formatDigits: (value: string | number) => string;
  formatDate: (iso: string) => string;
  formatDateTime: (value: Date) => string;
  formatHijriYear: (value?: Date) => string;
  formatRelativeTime: (iso: string, now?: Date) => string;
};

const NumeralContext = createContext<NumeralContextValue | null>(null);

export function NumeralProvider({ children }: { children: ReactNode }) {
  const numeralSystem = useSyncExternalStore(
    subscribe,
    getBrowserSnapshot,
    () => DEFAULT_NUMERAL_SYSTEM,
  );

  const setNumeralSystem = useCallback((system: NumeralSystem) => {
    saveNumeralSystem(system);
  }, []);

  const toggleNumeralSystem = useCallback(() => {
    saveNumeralSystem(numeralSystem === "arab" ? "latn" : "arab");
  }, [numeralSystem]);

  useEffect(() => {
    document.documentElement.dataset.numeralSystem = numeralSystem;
    document.documentElement.dataset.numeralReady = "true";
  }, [numeralSystem]);

  const value = useMemo<NumeralContextValue>(
    () => ({
      numeralSystem,
      setNumeralSystem,
      toggleNumeralSystem,
      formatNumber: (number, options) =>
        formatNumberValue(number, numeralSystem, options),
      formatDigits: (text) => formatDigitsValue(text, numeralSystem),
      formatDate: (iso) => formatDateValue(iso, numeralSystem),
      formatDateTime: (date) => formatDateTimeValue(date, numeralSystem),
      formatHijriYear: (date) => formatHijriYearValue(date, numeralSystem),
      formatRelativeTime: (iso, now) =>
        formatRelativeTimeValue(iso, now, numeralSystem),
    }),
    [numeralSystem, setNumeralSystem, toggleNumeralSystem],
  );

  return (
    <NumeralContext.Provider value={value}>{children}</NumeralContext.Provider>
  );
}

export function useNumerals(): NumeralContextValue {
  const context = useContext(NumeralContext);
  if (!context) {
    throw new Error("useNumerals must be used inside NumeralProvider");
  }
  return context;
}
