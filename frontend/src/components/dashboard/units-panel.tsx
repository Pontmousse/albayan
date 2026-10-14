"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Ruler, Trash2, X } from "lucide-react";

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
  area_volume: "المساحة والحجم", historical: "الوحدات التراثية",
  custom: "وحدات المقال", unknown: "وحدات غير معرّفة",
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

  useEffect(() => { if (open) void load(); }, [open, load]);

  const usedTokens = useMemo(
    () => new Set(inventory?.used_units.map((u) => u.token) ?? []),
    [inventory],
  );
  const customRows = Object.entries(settings.custom_units).sort(([a], [b]) => a.localeCompare(b));
  const orderedUsedUnits = useMemo(() => [...(inventory?.used_units ?? [])].sort(
    (a, b) => (a.group ?? a.status).localeCompare(b.group ?? b.status) || a.token.localeCompare(b.token),
  ), [inventory]);

  function setKnownDisplay(unit: UsedUnit, value: string) {
    if (value === "__custom__") {
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
      <header className="flex shrink-0 items-center justify-between border-b border-[var(--journal-border)] bg-white px-5 py-4">
        <div>
          <p className="text-xs font-semibold text-[var(--journal-accent-strong)]">اصطلاحات المقال</p>
          <h2 id="units-panel-title" className="mt-1 flex items-center gap-2 text-xl font-bold text-slate-900">
            <Ruler aria-hidden className="h-5 w-5" /> وحدات القياس
          </h2>
          <p className="mt-1 text-sm text-slate-600">اختر طريقة كتابة الوحدات دون تغيير قيمتها أو معناها.</p>
        </div>
        <button onClick={onClose} type="button" aria-label="إغلاق" className="rounded-full border border-[var(--journal-border)] p-2 text-slate-600">
          <X aria-hidden className="h-5 w-5" />
        </button>
      </header>
      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
        {error ? <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}
        {success ? <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">تم حفظ الاصطلاحات وتحديث المسودة الحالية.</p> : null}
        {loading || !inventory ? (
          <p className="py-12 text-center text-sm text-slate-500">جارٍ تحميل وحدات المقال…</p>
        ) : (
          <>
            <section>
              <h3 className="text-base font-bold text-slate-900">الوحدات المستخدمة ({formatDigits(String(inventory.used_units.length))})</h3>
              <p className="mt-1 text-xs text-slate-500">مستخرجة من المعادلات المنظمة، لا من أسماء المتغيرات أو النص العربي.</p>
              {inventory.used_units.length === 0 ? (
                <p className="mt-3 rounded-xl border border-dashed border-[var(--journal-border)] p-5 text-sm text-slate-500">لا توجد وحدات صريحة في معادلات المقال حالياً.</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {orderedUsedUnits.map((unit, index) => {
                    const group = unit.group ?? (unit.status === "custom" ? "custom" : "unknown");
                    const previous = orderedUsedUnits[index - 1];
                    const previousGroup = previous?.group ?? (previous?.status === "custom" ? "custom" : "unknown");
                    const showGroup = index === 0 || previousGroup !== group;
                    const override = settings.overrides[unit.token];
                    const isCustom = unit.status === "custom" || !!settings.custom_units[unit.token];
                    const chosen = override === undefined ? "__default__"
                      : override === unit.token ? "__international__"
                      : unit.alternatives.includes(override) ? override
                      : "__custom__";
                    const showCustom = customDisplays[unit.token] || chosen === "__custom__";
                    return (
                      <div key={unit.token} className="space-y-3">
                        {showGroup ? <h4 className="pt-2 text-sm font-bold text-slate-700">{GROUP_LABELS[group] ?? group}</h4> : null}
                        <div className="rounded-xl border border-[var(--journal-border)] bg-white p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-3">
                            <code dir="ltr" className="rounded-lg bg-slate-100 px-2 py-1 font-mono font-semibold text-slate-900">{unit.token}</code>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{unit.name_ar ?? unit.name ?? (isCustom ? "وحدة مخصصة" : "وحدة غير معرّفة")}</p>
                              <p className="text-xs text-slate-500">{stateLabel(unit)} · {formatDigits(String(unit.usage_count))} استعمال</p>
                            </div>
                          </div>
                          <span className="text-sm font-bold text-[var(--journal-accent-strong)]" dir="auto">
                            {isCustom ? settings.custom_units[unit.token]?.display : override ?? unit.display}
                          </span>
                        </div>
                        {unit.status === "unknown" && !isCustom ? (
                          <div className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                            وحدة غير موجودة في سجل برهان.
                            <button type="button" className="ms-2 font-bold underline" onClick={() => addCustom(unit.token, "", unit.token)}>
                              تعريف وحدة مخصصة
                            </button>
                          </div>
                        ) : unit.status === "registry" ? (
                          <div className="mt-3 grid gap-2 sm:grid-cols-2 sm:items-center">
                            <label className="text-xs font-semibold text-slate-600" htmlFor={`unit-${unit.token}`}>كيفية العرض</label>
                            <select id={`unit-${unit.token}`} className={fieldClass}
                              value={showCustom ? "__custom__" : chosen}
                              onChange={(event) => setKnownDisplay(unit, event.target.value)}>
                              <option value="__default__">البيان الافتراضي — {unit.default_display}</option>
                              {unit.alternatives.map((alt) => <option key={alt} value={alt}>{alt}</option>)}
                              <option value="__international__">الرمز الدولي — {unit.token}</option>
                              <option value="__custom__">كتابة مخصصة…</option>
                            </select>
                            {showCustom ? (
                              <input className={`${fieldClass} sm:col-start-2`} aria-label={`كتابة مخصصة للوحدة ${unit.token}`}
                                value={override ?? ""} maxLength={64}
                                onChange={(event) => setOverride(unit.token, event.target.value)} />
                            ) : null}
                          </div>
                        ) : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
            <section className="border-t border-[var(--journal-border)] pt-5">
              <h3 className="text-base font-bold text-slate-900">وحداتي المخصصة</h3>
              <p className="mt-1 text-xs leading-5 text-slate-500">يمكن تعديل اسم الوحدة وعرضها، لكن رمزها القانوني لا يُغيّر إلا بتعديل المعادلات نفسها.</p>
              <div className="mt-3 space-y-3">
                {customRows.map(([token, definition]) => (
                  <div key={token} className="rounded-xl border border-[var(--journal-border)] bg-white p-3">
                    <div className="flex items-center justify-between gap-3">
                      <code dir="ltr" className="font-semibold">{token}</code>
                      <button type="button" onClick={() => removeCustom(token)}
                        aria-label={`حذف الوحدة ${token}`} disabled={usedTokens.has(token)}
                        title={usedTokens.has(token) ? "وحدة مستخدمة؛ عدّل المعادلات قبل حذفها" : "حذف الوحدة"}
                        className="rounded-lg p-2 text-red-700 disabled:cursor-not-allowed disabled:opacity-40">
                        <Trash2 aria-hidden className="h-4 w-4" />
                      </button>
                    </div>
                    {usedTokens.has(token) ? <p className="mt-1 text-xs text-amber-800">مستخدمة في المعادلات، لا يمكن حذفها.</p> : null}
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <label className="text-xs font-semibold text-slate-600">الاسم (اختياري)
                        <input className={`${fieldClass} mt-1`} value={definition.name ?? ""}
                          maxLength={100} onChange={(event) => setCustom(token, { name: event.target.value || undefined })} />
                      </label>
                      <label className="text-xs font-semibold text-slate-600">العرض
                        <input className={`${fieldClass} mt-1`} value={definition.display}
                          maxLength={64} onChange={(event) => setCustom(token, { display: event.target.value })} />
                      </label>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-xl border border-dashed border-[var(--journal-border)] bg-slate-50 p-4">
                <p className="mb-3 text-sm font-bold text-slate-800">إضافة وحدة مخصصة</p>
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="text-xs font-semibold text-slate-600">الرمز القانوني
                    <input dir="ltr" className={`${fieldClass} mt-1`} placeholder="CU" value={newToken}
                      onChange={(event) => setNewToken(event.target.value)} />
                  </label>
                  <label className="text-xs font-semibold text-slate-600">الاسم (اختياري)
                    <input className={`${fieldClass} mt-1`} placeholder="Calibration unit" value={newName}
                      onChange={(event) => setNewName(event.target.value)} />
                  </label>
                  <label className="text-xs font-semibold text-slate-600">العرض
                    <input className={`${fieldClass} mt-1`} placeholder="وحدة معايرة" value={newDisplay}
                      onChange={(event) => setNewDisplay(event.target.value)} />
                  </label>
                </div>
                <button type="button" onClick={() => addCustom()}
                  className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-4 text-sm font-bold text-[var(--journal-accent-strong)]">
                  <Plus aria-hidden className="h-4 w-4" /> إضافة الوحدة
                </button>
              </div>
            </section>
          </>
        )}
      </div>
      <footer className="flex shrink-0 items-center justify-end gap-3 border-t border-[var(--journal-border)] bg-white p-4">
        <button type="button" onClick={onClose} className="min-h-10 rounded-lg border border-[var(--journal-border)] px-4 text-sm font-semibold text-slate-700">إغلاق</button>
        <button type="button" disabled={!inventory || loading || saving} onClick={() => void save()}
          className="min-h-10 rounded-lg bg-[var(--journal-accent-strong)] px-5 text-sm font-semibold text-white disabled:opacity-50">
          {saving ? "جارٍ التطبيق…" : "حفظ وتطبيق"}
        </button>
      </footer>
    </AnimatedOverlay>
  );
}
