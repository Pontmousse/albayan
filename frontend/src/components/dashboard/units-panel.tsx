"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight, Check, ChevronDown, ChevronLeft, CircleHelp, Clock3, Cog,
  FlaskConical, Gauge, Orbit, Pencil, Plus, Puzzle, Ruler,
  Scale, Shapes, Sun, Thermometer, Trash2, X, Zap,
  type LucideIcon,
} from "lucide-react";

import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import { useNumerals } from "@/components/numeral-provider";
import {
  applyUnitConventions, getUsedUnits,
  type UnitConventions, type UnitInventory, type UsedUnit,
} from "@/lib/api/units";
import { ApiError } from "@/lib/api";
import { validateUnitConventions } from "@/lib/unit-conventions";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";
import type { DraftRevision } from "@/lib/api/articles";

type GetToken = () => Promise<string | null>;
const EMPTY: UnitConventions = { overrides: {}, custom_units: {} };
const GROUP_LABELS: Record<string, string> = {
  length: "الطول", mass: "الكتلة", time: "الزمن والتردد",
  electricity: "الكهرباء والمغناطيسية", temperature: "درجة الحرارة",
  chemistry: "كمية المادة", light: "الضوء", mechanics: "الميكانيكا",
  energy_power: "الطاقة والقدرة", angles: "الزوايا",
  area_volume: "المساحة والحجم",
  custom: "وحداتي المخصصة", unknown: "وحدات غير معرّفة",
};
const GROUP_ICONS: Record<string, LucideIcon> = {
  length: Ruler, mass: Scale, time: Clock3, electricity: Zap,
  temperature: Thermometer, chemistry: FlaskConical, light: Sun,
  mechanics: Cog, energy_power: Gauge, angles: Orbit,
  area_volume: Shapes, custom: Puzzle, unknown: CircleHelp,
};
const fieldClass = "min-h-10 w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 text-sm text-slate-900 outline-none focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent-soft)]";

function stateLabel(unit: UsedUnit) {
  if (unit.source === "article_override") return "مخصّصة";
  if (unit.source === "article_custom") return "وحدة المقال";
  if (unit.source === "unknown") return "غير معرّفة";
  return "البيان الافتراضي";
}

export function UnitsPanel({
  open, articleId, getToken, onClose, onBeforeApply, onApplied,
}: {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  onClose: () => void;
  onBeforeApply: () => Promise<number>;
  onApplied: (revision: DraftRevision) => void;
}) {
  const { formatDigits } = useNumerals();
  const [inventory, setInventory] = useState<UnitInventory | null>(null);
  const [settings, setSettings] = useState<UnitConventions>(EMPTY);
  const [customDisplays, setCustomDisplays] = useState<Record<string, boolean>>({});
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [editingToken, setEditingToken] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [newToken, setNewToken] = useState("");
  const [newName, setNewName] = useState("");
  const [newDisplay, setNewDisplay] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const data = await getUsedUnits(getToken, articleId);
      setInventory(data);
      setSettings(data.unit_conventions);
      setCustomDisplays({});
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل وحدات المقال."));
    } finally {
      setLoading(false);
    }
  }, [articleId, getToken]);

  useEffect(() => {
    if (!open) return;
    setSelectedGroup(null);
    setEditingToken(null);
    void load();
  }, [open, load]);

  const usedTokens = useMemo(
    () => new Set(inventory?.used_units.map((u) => u.token) ?? []),
    [inventory],
  );
  const groups = useMemo(() => {
    const buckets = new Map<string, UsedUnit[]>();
    for (const unit of inventory?.used_units ?? []) {
      // Custom definitions have their own editor; do not show them twice.
      if (unit.status === "custom" || settings.custom_units[unit.token]) continue;
      const key = unit.group ?? "unknown";
      buckets.set(key, [...(buckets.get(key) ?? []), unit]);
    }
    return Array.from(buckets, ([key, units]) => ({
      key, units: units.sort((a, b) => a.token.localeCompare(b.token)),
    })).sort((a, b) => (GROUP_LABELS[a.key] ?? a.key).localeCompare(GROUP_LABELS[b.key] ?? b.key, "ar"));
  }, [inventory, settings.custom_units]);
  const currentGroup = groups.find((group) => group.key === selectedGroup);
  const customRows = Object.entries(settings.custom_units).sort(([a], [b]) => a.localeCompare(b));

  function navigateToGroup(group: string | null) {
    setSelectedGroup(group);
    setEditingToken(null);
    contentRef.current?.scrollTo({ top: 0 });
  }

  function chooseKnownDisplay(unit: UsedUnit, value: string) {
    setKnownDisplay(unit, value);
    if (value !== "__custom__") setEditingToken(null);
  }

  function setKnownDisplay(unit: UsedUnit, value: string) {
    if (value === "__custom__") {
      setSuccess(false);
      setCustomDisplays((previous) => ({ ...previous, [unit.token]: true }));
      setSettings((previous) => ({
        ...previous,
        overrides: { ...previous.overrides, [unit.token]: previous.overrides[unit.token] ?? unit.display },
      }));
      return;
    }
    setCustomDisplays((previous) => ({ ...previous, [unit.token]: false }));
    setSettings((previous) => {
      const overrides = { ...previous.overrides };
      if (value === "__default__") delete overrides[unit.token];
      else overrides[unit.token] = value === "__international__" ? unit.token : value;
      return { ...previous, overrides };
    });
    setSuccess(false);
  }

  function setOverride(token: string, display: string) {
    setSettings((previous) => ({
      ...previous,
      overrides: { ...previous.overrides, [token]: display },
    }));
    setSuccess(false);
  }

  function setCustom(token: string, patch: { name?: string; display?: string }) {
    setSettings((previous) => ({
      ...previous,
      custom_units: {
        ...previous.custom_units,
        [token]: { ...previous.custom_units[token], ...patch },
      },
    }));
    setSuccess(false);
  }

  function addCustom(token = newToken, name = newName, display = newDisplay) {
    const normalized = token.trim();
    if (!/^[A-Za-z][A-Za-z0-9]*$/.test(normalized)) {
      setError("رمز الوحدة يجب أن يبدأ بحرف لاتيني، ثم حروف أو أرقام فقط.");
      return;
    }
    if (inventory?.registered_tokens.includes(normalized)) {
      setError("هذه وحدة مسجّلة؛ يمكنك تغيير طريقة عرضها دون إعادة تعريفها.");
      return;
    }
    if (settings.custom_units[normalized]) {
      setError("هذه الوحدة المخصصة معرّفة بالفعل.");
      return;
    }
    if (!display.trim()) {
      setError("أدخل كيفية عرض الوحدة أولاً.");
      return;
    }
    const next: UnitConventions = {
      ...settings,
      custom_units: {
        ...settings.custom_units,
        [normalized]: { display, ...(name.trim() ? { name: name.trim() } : {}) },
      },
    };
    try {
      validateUnitConventions(next, inventory?.registered_tokens ?? [], Array.from(usedTokens));
      setSettings(next);
      setNewToken("");
      setNewName("");
      setNewDisplay("");
      setError(null);
      setSuccess(false);
      navigateToGroup("custom");
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر إضافة الوحدة."));
    }
  }

  function removeCustom(token: string) {
    if (usedTokens.has(token)) {
      setError(`لا يمكن حذف «${token}» لأنها مستخدمة في المعادلات. عدّل المعادلات أولاً.`);
      return;
    }
    setSettings((previous) => {
      const custom_units = { ...previous.custom_units };
      delete custom_units[token];
      return { ...previous, custom_units };
    });
    setSuccess(false);
  }

  async function save() {
    if (!inventory) return;
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const next = validateUnitConventions(
        settings, inventory.registered_tokens, Array.from(usedTokens),
        inventory.unit_conventions,
      );
      // Flush browser edits before touching server-side Document2. The server
      // checks the base revision and rejects concurrent changes atomically.
      const baseRevision = await onBeforeApply();
      const revision = await applyUnitConventions(getToken, articleId, baseRevision, next);
      onApplied(revision);
      await load();
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("تغيّرت المسودة أو اصطلاحات الوحدات؛ أعد فتح اللوحة بعد تحديث المقال.");
      } else {
        setError(userFacingErrorMessage(err, "تعذّر تطبيق اصطلاحات الوحدات."));
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatedOverlay
      open={open}
      onClose={onClose}
      labelledBy="units-panel-title"
      mobileFullscreen
      panelClassName="!p-0 flex h-dvh max-h-dvh flex-col overflow-hidden md:h-[min(92dvh,52rem)] md:max-w-3xl"
    >
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--journal-border)] bg-[var(--journal-paper)] px-4 py-4 sm:px-6">
        <div className="min-w-0">
          <p className="text-xs font-semibold text-[var(--journal-accent-strong)]">اصطلاحات المقال</p>
          <h2 id="units-panel-title" className="mt-1 flex items-center gap-2 text-xl font-bold text-slate-900">
            <Ruler aria-hidden className="h-5 w-5 shrink-0" /> وحدات القياس
          </h2>
          <p className="mt-1 text-xs leading-6 text-slate-600 sm:text-sm">اختر طريقة كتابة الوحدات دون تغيير قيمتها أو معناها.</p>
        </div>
        <button onClick={onClose} type="button" aria-label="إغلاق"
          className="flex size-11 shrink-0 items-center justify-center rounded-full border border-[var(--journal-border)] bg-white text-slate-600 transition hover:bg-[var(--journal-accent-soft)] focus-visible:outline-2 focus-visible:outline-[var(--journal-accent)]">
          <X aria-hidden className="h-5 w-5" />
        </button>
      </header>

      <div ref={contentRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain bg-[var(--journal-paper)] p-4 sm:p-6">
        {error ? <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}
        {success ? <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">تم حفظ الاصطلاحات وتحديث المسودة الحالية.</p> : null}
        {loading || !inventory ? (
          <p className="py-12 text-center text-sm text-slate-500">جارٍ تحميل وحدات المقال…</p>
        ) : selectedGroup === null ? (
          <section aria-label="مجموعات وحدات القياس">
            <div className="mb-5">
              <h3 className="text-lg font-bold text-slate-900">استعرض الوحدات حسب المجال</h3>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                {formatDigits(String(inventory.used_units.length))} وحدة مستخدمة في المعادلات. اختر مجموعة لعرض وحداتها وتعديلها.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {groups.map((group) => {
                const Icon = GROUP_ICONS[group.key] ?? Ruler;
                return (
                  <button key={group.key} type="button" onClick={() => navigateToGroup(group.key)}
                    className="group flex min-h-32 flex-col justify-between gap-4 rounded-2xl border border-[var(--journal-border)] bg-white p-4 text-start shadow-sm transition hover:border-[var(--journal-accent)] hover:shadow-md focus-visible:outline-2 focus-visible:outline-[var(--journal-accent)]">
                    <div className="flex w-full items-start gap-3">
                      <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
                        <Icon aria-hidden className="h-5 w-5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="font-bold leading-6 text-slate-900">{GROUP_LABELS[group.key] ?? group.key}</p>
                        <p className="mt-0.5 text-xs text-slate-500">{formatDigits(String(group.units.length))} وحدة</p>
                      </div>
                      <ChevronLeft aria-hidden className="mt-3 h-4 w-4 shrink-0 text-slate-400 transition group-hover:text-[var(--journal-accent)]" />
                    </div>
                    <div className="flex max-w-full flex-wrap gap-1.5" dir="ltr">
                      {group.units.slice(0, 4).map((unit) => (
                        <span key={unit.token} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{unit.token}</span>
                      ))}
                      {group.units.length > 4 ? <span className="px-1 py-1 text-xs text-slate-400">+{formatDigits(String(group.units.length - 4))}</span> : null}
                    </div>
                  </button>
                );
              })}
              <button type="button" onClick={() => navigateToGroup("custom")}
                className="group flex min-h-32 flex-col justify-between gap-4 rounded-2xl border border-[var(--journal-border)] bg-white p-4 text-start shadow-sm transition hover:border-[var(--journal-accent)] hover:shadow-md focus-visible:outline-2 focus-visible:outline-[var(--journal-accent)]">
                <div className="flex w-full items-start gap-3">
                  <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
                    <Puzzle aria-hidden className="h-5 w-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-bold text-slate-900">وحداتي المخصصة</p>
                    <p className="mt-0.5 text-xs text-slate-500">{formatDigits(String(customRows.length))} وحدة معرّفة</p>
                  </div>
                  <ChevronLeft aria-hidden className="mt-3 h-4 w-4 shrink-0 text-slate-400 transition group-hover:text-[var(--journal-accent)]" />
                </div>
                <p className="text-xs text-slate-500">إضافة وحدات جديدة وتعديل تعريفاتها</p>
              </button>
            </div>
            {inventory.used_units.length === 0 ? (
              <p className="mt-5 rounded-xl border border-dashed border-[var(--journal-border)] bg-white p-4 text-sm text-slate-600">لا توجد وحدات صريحة في المعادلات حالياً. يمكنك إضافة وحدات مخصصة من البطاقة أعلاه.</p>
            ) : null}
          </section>
        ) : (
          <>
            <nav aria-label="التنقل بين مجموعات الوحدات">
              <button type="button" onClick={() => navigateToGroup(null)}
                className="inline-flex min-h-11 items-center gap-2 rounded-lg px-2 text-sm font-semibold text-[var(--journal-accent-strong)] transition hover:bg-[var(--journal-accent-soft)] focus-visible:outline-2 focus-visible:outline-[var(--journal-accent)]">
                <ArrowRight aria-hidden className="h-4 w-4" /> جميع المجموعات
              </button>
            </nav>
            <div className="flex items-center gap-3 border-b border-[var(--journal-border)] pb-4">
              {(() => {
                const Icon = GROUP_ICONS[selectedGroup] ?? Ruler;
                return (
                  <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
                    <Icon aria-hidden className="h-6 w-6" />
                  </span>
                );
              })()}
              <div className="min-w-0">
                <h3 className="text-lg font-bold text-slate-900">{GROUP_LABELS[selectedGroup] ?? selectedGroup}</h3>
                <p className="text-xs leading-6 text-slate-500">
                  {selectedGroup === "custom"
                    ? "تعريف وحدات المقال وتعديل أسمائها وطريقة عرضها."
                    : formatDigits(String(currentGroup?.units.length ?? 0)) + " وحدة مستخدمة · اختر تغيير لتخصيص العرض."}
                </p>
              </div>
            </div>

            {selectedGroup !== "custom" ? (
              <section className="space-y-4" aria-label="وحدات المجموعة">
                {(currentGroup?.units ?? []).map((unit) => {
                  const override = settings.overrides[unit.token];
                  const chosen = override === undefined ? "__default__"
                    : override === unit.token ? "__international__"
                    : unit.alternatives.includes(override) ? override
                    : "__custom__";
                  const customMode = customDisplays[unit.token] || chosen === "__custom__";
                  const isEditing = editingToken === unit.token;
                  const display = override ?? unit.default_display ?? unit.display;
                  const alternatives = unit.alternatives.filter((alternative) =>
                    alternative !== unit.default_display && alternative !== unit.token
                  );
                  const choices = [
                    { value: "__default__", label: "البيان الافتراضي", display: unit.default_display ?? unit.display },
                    { value: "__international__", label: "الرمز الدولي", display: unit.token },
                    ...alternatives.map((value) => ({ value, label: "صيغة بديلة", display: value })),
                  ];
                  return (
                    <article key={unit.token} className="overflow-hidden rounded-2xl border border-[var(--journal-border)] bg-white shadow-sm">
                      <div className="space-y-4 p-4 sm:p-5">
                        <div className="flex flex-wrap items-start gap-3">
                          <span dir="ltr" className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm font-bold text-slate-800">{unit.token}</span>
                          <div className="min-w-0 flex-1">
                            <h4 className="text-base font-bold leading-7 text-slate-900">{unit.name_ar ?? unit.name ?? "وحدة غير معرّفة"}</h4>
                            <p className="text-xs text-slate-500">{formatDigits(String(unit.usage_count))} استعمال · {stateLabel(unit)}</p>
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3">
                          <div className="min-w-0">
                            <p className="text-xs text-slate-500">العرض الحالي</p>
                            <p dir="auto" className="mt-1 text-base font-bold text-[var(--journal-accent-strong)]">{display}</p>
                          </div>
                          {unit.status === "registry" ? (
                            <button type="button" aria-expanded={isEditing} aria-controls={"unit-options-" + unit.token}
                              onClick={() => setEditingToken(isEditing ? null : unit.token)}
                              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-[var(--journal-border)] bg-[var(--journal-paper)] px-4 text-sm font-bold text-[var(--journal-accent-strong)] transition hover:border-[var(--journal-accent)] focus-visible:outline-2 focus-visible:outline-[var(--journal-accent)]">
                              <Pencil aria-hidden className="h-4 w-4" /> تغيير
                              <ChevronDown aria-hidden className={isEditing ? "h-4 w-4 rotate-180" : "h-4 w-4"} />
                            </button>
                          ) : null}
                        </div>
                        {unit.status === "unknown" ? (
                          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                            هذه الوحدة غير موجودة في سجل برهان.
                            <button type="button" className="ms-2 font-bold underline" onClick={() => addCustom(unit.token, "", unit.token)}>تعريف وحدة مخصصة</button>
                          </div>
                        ) : null}
                      </div>
                      {unit.status === "registry" && isEditing ? (
                        <div id={"unit-options-" + unit.token} className="space-y-3 border-t border-[var(--journal-border)] bg-[var(--journal-paper)] p-4 sm:p-5">
                          <p className="text-sm font-semibold text-slate-800">اختر طريقة عرض الوحدة</p>
                          <div role="group" aria-label={"خيارات عرض " + unit.token} className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                            {choices.map((choice) => {
                              const active = !customMode && chosen === choice.value;
                              return (
                                <button key={choice.value} type="button" aria-pressed={active}
                                  onClick={() => chooseKnownDisplay(unit, choice.value)}
                                  className={active
                                    ? "flex min-h-16 items-center justify-between gap-3 rounded-xl border-2 border-[var(--journal-accent)] bg-white p-3 text-start shadow-sm"
                                    : "flex min-h-16 items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white p-3 text-start transition hover:border-[var(--journal-accent)]"}>
                                  <span className="min-w-0">
                                    <span className="block text-xs text-slate-500">{choice.label}</span>
                                    <span dir="auto" className="mt-1 block font-bold text-slate-900">{choice.display}</span>
                                  </span>
                                  {active ? <Check aria-hidden className="h-5 w-5 shrink-0 text-[var(--journal-accent)]" /> : null}
                                </button>
                              );
                            })}
                            <button type="button" aria-pressed={customMode} onClick={() => chooseKnownDisplay(unit, "__custom__")}
                              className={customMode
                                ? "flex min-h-16 items-center justify-between gap-3 rounded-xl border-2 border-[var(--journal-accent)] bg-white p-3 text-start shadow-sm"
                                : "flex min-h-16 items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white p-3 text-start transition hover:border-[var(--journal-accent)]"}>
                              <span>
                                <span className="block text-xs text-slate-500">كتابة مخصصة</span>
                                <span className="mt-1 block font-bold text-slate-900">أدخل صياغتك</span>
                              </span>
                              {customMode ? <Check aria-hidden className="h-5 w-5 shrink-0 text-[var(--journal-accent)]" /> : null}
                            </button>
                          </div>
                          {customMode ? (
                            <label className="block text-sm font-semibold text-slate-700">
                              كتابة الوحدة
                              <input className={fieldClass + " mt-2"} dir="auto" value={override ?? ""} maxLength={64}
                                onChange={(event) => setOverride(unit.token, event.target.value)} />
                            </label>
                          ) : null}
                        </div>
                      ) : null}
                    </article>
                  );
                })}
              </section>
            ) : (
              <section className="space-y-4" aria-label="الوحدات المخصصة">
                {customRows.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-[var(--journal-border)] bg-white p-4 text-sm text-slate-600">لم تضف وحدات مخصصة بعد.</p>
                ) : null}
                {customRows.map(([token, definition]) => {
                  const usage = inventory.used_units.find((unit) => unit.token === token)?.usage_count ?? 0;
                  return (
                    <article key={token} className="space-y-4 rounded-2xl border border-[var(--journal-border)] bg-white p-4 shadow-sm sm:p-5">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <code dir="ltr" className="rounded-lg bg-slate-100 px-3 py-2 font-mono font-semibold text-slate-800">{token}</code>
                          <span className="text-xs text-slate-500">{formatDigits(String(usage))} استعمال</span>
                        </div>
                        <button type="button" onClick={() => removeCustom(token)} aria-label={"حذف " + token}
                          disabled={usedTokens.has(token)} title={usedTokens.has(token) ? "هذه الوحدة مستخدمة في المعادلات" : "حذف الوحدة"}
                          className="flex size-11 items-center justify-center rounded-lg text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40">
                          <Trash2 aria-hidden className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <label className="block text-sm font-semibold text-slate-700">
                          الاسم (اختياري)
                          <input className={fieldClass + " mt-2"} value={definition.name ?? ""} maxLength={100}
                            onChange={(event) => setCustom(token, { name: event.target.value || undefined })} />
                        </label>
                        <label className="block text-sm font-semibold text-slate-700">
                          طريقة العرض
                          <input className={fieldClass + " mt-2"} value={definition.display} maxLength={64}
                            onChange={(event) => setCustom(token, { display: event.target.value })} />
                        </label>
                      </div>
                    </article>
                  );
                })}
                <div className="space-y-4 rounded-2xl border border-dashed border-[var(--journal-border)] bg-white p-4 sm:p-5">
                  <div className="flex items-center gap-2">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"><Plus aria-hidden className="h-5 w-5" /></span>
                    <h4 className="font-bold text-slate-900">إضافة وحدة مخصصة</h4>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <label className="block text-sm font-semibold text-slate-700">
                      الرمز الدولي
                      <input dir="ltr" className={fieldClass + " mt-2"} placeholder="CU" value={newToken}
                        onChange={(event) => setNewToken(event.target.value)} />
                    </label>
                    <label className="block text-sm font-semibold text-slate-700">
                      الاسم (اختياري)
                      <input className={fieldClass + " mt-2"} placeholder="Calibration unit" value={newName}
                        onChange={(event) => setNewName(event.target.value)} />
                    </label>
                    <label className="block text-sm font-semibold text-slate-700">
                      طريقة العرض
                      <input className={fieldClass + " mt-2"} placeholder="وحدة معايرة" value={newDisplay}
                        onChange={(event) => setNewDisplay(event.target.value)} />
                    </label>
                  </div>
                  <button type="button" onClick={() => addCustom()}
                    className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[var(--journal-accent-strong)] px-4 text-sm font-bold text-white transition hover:opacity-90">
                    <Plus aria-hidden className="h-4 w-4" /> إضافة الوحدة
                  </button>
                </div>
              </section>
            )}
          </>
        )}
      </div>
      <footer className="flex shrink-0 items-center justify-end gap-3 border-t border-[var(--journal-border)] bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-6">
        <button type="button" onClick={onClose} className="min-h-11 rounded-xl border border-[var(--journal-border)] px-4 text-sm font-semibold text-slate-600 hover:bg-slate-50">إغلاق</button>
        <button type="button" disabled={!inventory || loading || saving} onClick={() => void save()}
          className="min-h-11 rounded-xl bg-[var(--journal-accent-strong)] px-5 text-sm font-bold text-white transition hover:opacity-90 disabled:opacity-50">
          {saving ? "جارٍ التطبيق…" : "حفظ وتطبيق"}
        </button>
      </footer>
    </AnimatedOverlay>
  );
}
