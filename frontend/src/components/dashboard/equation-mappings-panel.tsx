"use client";

import {
  ArrowLeftRight,
  ArrowUpLeft,
  Plus,
  Sigma,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { MappingFontSelector } from "@/components/dashboard/mapping-font-selector";
import { useNumerals } from "@/components/numeral-provider";
import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import { CopyButton } from "@/components/ui/copy-button";
import {
  getEquationMappings,
  putEquationMappings,
} from "@/lib/api/equation-mappings";
import { isDevMode } from "@/lib/dev-mode";
import {
  equationMappingRows,
  equationMappingsFromRows,
  type EquationMappingRow,
} from "@/lib/equation-mappings";
import {
  serializeMappingTarget,
  type EditableMappingFontId,
} from "@/lib/mapping-fonts";
import {
  UserFacingError,
  userFacingErrorMessage,
} from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;
type EditableEquationMappingRow = EquationMappingRow & { id: string };

export function EquationMappingsPanel({
  open,
  articleId,
  getToken,
  onClose,
}: {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  onClose: () => void;
}) {
  const { formatDigits } = useNumerals();
  const showTechnicalPreview = isDevMode();
  const [rows, setRows] = useState<EditableEquationMappingRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const nextRowId = useRef(0);
  const listRef = useRef<HTMLDivElement>(null);

  const createEditableRow = useCallback(
    (
      row: EquationMappingRow = {
        english: "",
        arabic: "",
        fontId: "default",
      },
    ) => ({
      ...row,
      id: `equation-mapping-${nextRowId.current++}`,
    }),
    [],
  );

  const load = useCallback(async () => {
    setError(null);
    setSaved(false);
    setRows(null);
    try {
      const response = await getEquationMappings(getToken, articleId);
      setRows(equationMappingRows(response.mappings).map(createEditableRow));
    } catch (err) {
      setRows([]);
      setError(userFacingErrorMessage(err, "تعذّر تحميل رموز المقال."));
    }
  }, [articleId, createEditableRow, getToken]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  function updateRow(index: number, patch: Partial<EquationMappingRow>) {
    setSaved(false);
    setRows((current) =>
      (current ?? []).map((row, rowIndex) =>
        rowIndex === index ? { ...row, ...patch } : row,
      ),
    );
  }

  function updateTarget(index: number, value: string) {
    setSaved(false);
    setRows((current) =>
      (current ?? []).map((row, rowIndex) => {
        if (rowIndex !== index) return row;
        if (row.fontId === "custom") {
          return {
            ...row,
            arabic: value,
            fontId: "default",
            legacySerialized: undefined,
          };
        }
        return { ...row, arabic: value };
      }),
    );
  }

  function updateFont(index: number, fontId: EditableMappingFontId) {
    updateRow(index, {
      fontId,
      ...(fontId === "custom" ? {} : { legacySerialized: undefined }),
    });
  }

  function addRow() {
    setSaved(false);
    const row = createEditableRow();
    setRows((current) => [...(current ?? []), row]);
    requestAnimationFrame(() => {
      document.getElementById(`${row.id}-original`)?.focus();
      listRef.current?.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }

  function removeRow(index: number) {
    setSaved(false);
    setRows((current) =>
      (current ?? []).filter((_, rowIndex) => rowIndex !== index),
    );
  }

  async function save() {
    if (rows === null) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const mappings = equationMappingsFromRows(rows);
      const response = await putEquationMappings(getToken, articleId, mappings);
      setRows(equationMappingRows(response.mappings).map(createEditableRow));
      setSaved(true);
    } catch (err) {
      setError(
        err instanceof UserFacingError
          ? userFacingErrorMessage(err, "تعذّر حفظ رموز المقال.")
          : userFacingErrorMessage(
              err,
              "تعذّر حفظ رموز المقال. حاول مجدداً.",
            ),
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatedOverlay
      open={open}
      onClose={onClose}
      labelledBy="equation-mappings-title"
      mobileFullscreen
      panelClassName="!p-0 flex h-dvh max-h-dvh flex-col overflow-hidden md:h-[min(94dvh,56rem)] md:max-h-[94dvh] md:max-w-5xl lg:h-[min(86dvh,52rem)]"
    >
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--journal-border)] bg-white/85 px-4 py-3 sm:px-5 md:px-6 md:py-5">
        <div className="min-w-0">
          <p className="hidden text-xs font-semibold text-[var(--journal-accent-strong)] md:block">
            اصطلاحات المقال
          </p>
          <h2
            id="equation-mappings-title"
            className="text-lg font-bold text-slate-900 md:mt-1 md:text-xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            رموز المعادلات
          </h2>
          <p className="mt-1 hidden text-sm leading-6 text-slate-600 sm:block">
            اختر الصيغة العربية التي تفضّلها لرموز مقالك.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="إغلاق"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--journal-border)] bg-white text-slate-500 transition hover:border-[var(--journal-accent)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
        >
          <X aria-hidden className="h-4 w-4" />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain lg:grid lg:grid-cols-[18rem_minmax(0,1fr)] lg:overflow-hidden">
        <div className="mx-4 mt-4 rounded-xl border border-emerald-200/80 bg-emerald-50/75 px-4 py-3 lg:hidden">
          <div className="flex items-start gap-2.5">
            <Sparkles
              aria-hidden
              className="mt-1 h-4 w-4 shrink-0 text-emerald-700"
            />
            <p className="text-sm leading-6 text-emerald-950">
              تساعد اختياراتك أدوات البيان الذكية على فهم اصطلاحات مقالك الرياضية بصورة أدق، وتُسهم في تطوير أدوات مستقبلية أفضل للرياضيات العربية.
            </p>
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-600">
            تبقى المعادلات الحالية كما هي، وتُستخدم اختياراتك في التعديلات والتحويلات القادمة.
          </p>
          <Link
            href="/wukala"
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--journal-accent-strong)] underline-offset-4 hover:underline"
          >
            تعرّف إلى وكلاء البيان
            <ArrowUpLeft aria-hidden className="h-3.5 w-3.5" />
          </Link>
        </div>

        <aside className="hidden border-l border-[var(--journal-border)] bg-gradient-to-b from-[var(--journal-accent-soft)]/75 to-white px-6 py-6 lg:block">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--journal-accent-strong)] text-white shadow-sm">
              <Sigma aria-hidden className="h-5 w-5" />
            </span>
            <div>
              <h3 className="font-bold text-slate-900">اصطلاحاتك الرياضية</h3>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                عيّن لكل رمز أصلي قيمته العربية والخط الذي تفضّله؛ لتفهم أدوات البيان اصطلاحات المقال بصورة أدق.
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-emerald-200/80 bg-emerald-50/80 p-3.5 text-sm leading-6 text-emerald-950">
            <div className="flex items-start gap-2.5">
              <Sparkles
                aria-hidden
                className="mt-1 h-4 w-4 shrink-0 text-emerald-700"
              />
              <p>
                مساهمتك تساعد على تطوير أدوات ونماذج مستقبلية أكثر فهماً للرياضيات المكتوبة بالعربية.
              </p>
            </div>
          </div>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            تسري الاختيارات على التعديلات والتحويلات القادمة فقط؛ وتبقى المعادلات الحالية كما هي.
          </p>

          <Link
            href="/wukala"
            className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white px-3.5 py-3 text-sm font-semibold text-[var(--journal-accent-strong)] shadow-sm transition hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md"
          >
            <span>تعرّف إلى وكلاء البيان</span>
            <ArrowUpLeft aria-hidden className="h-4 w-4 shrink-0" />
          </Link>

          <div className="mt-5 border-t border-[var(--journal-border)] pt-4">
            <p className="text-xs font-semibold text-slate-500">عدد الرموز</p>
            <p className="mt-1 text-2xl font-bold text-[var(--journal-accent-strong)]">
              {rows === null ? "—" : formatDigits(String(rows.length))}
            </p>
          </div>
        </aside>

        <section className="min-w-0 bg-white/45 lg:flex lg:min-h-0 lg:flex-col">
          <div className="flex items-center justify-between gap-3 border-b border-[var(--journal-border)] px-4 py-3 sm:px-5">
            <div>
              <h3 className="text-sm font-bold text-slate-800">قائمة الرموز</h3>
              <p className="mt-0.5 text-xs text-slate-500">
                {rows === null
                  ? "جارٍ التحميل…"
                  : rows.length === 0
                    ? "لا توجد رموز مضافة"
                    : `${formatDigits(String(rows.length))} ${rows.length === 1 ? "رمز" : "رموز"}`}
              </p>
            </div>
            <button
              type="button"
              onClick={addRow}
              disabled={rows === null}
              className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg bg-[var(--journal-accent-strong)] px-3.5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
            >
              <Plus aria-hidden className="h-4 w-4" />
              <span className="hidden sm:inline">إضافة رمز</span>
              <span className="sm:hidden">إضافة</span>
            </button>
          </div>

          {error ? (
            <p
              className="mx-4 mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 sm:mx-5"
              role="alert"
            >
              {error}
            </p>
          ) : null}
          {saved ? (
            <p
              className="mx-4 mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 sm:mx-5"
              role="status"
            >
              حُفظت رموز المقال.
            </p>
          ) : null}

          <div
            ref={listRef}
            className="equation-mappings-scrollbar space-y-3 px-4 py-4 sm:px-5 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:overscroll-contain"
          >
            {rows === null ? (
              <div className="space-y-3" aria-label="جارٍ تحميل الرموز">
                <div className="h-36 animate-pulse rounded-xl bg-slate-100" />
                <div className="h-36 animate-pulse rounded-xl bg-slate-100" />
              </div>
            ) : rows.length === 0 ? (
              <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--journal-border)] bg-white/80 p-6 text-center">
                <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
                  <Sigma aria-hidden className="h-7 w-7" />
                </span>
                <p className="mt-4 font-semibold text-slate-800">ابدأ بإضافة أول رمز</p>
                <p className="mt-1 text-sm text-slate-500">
                  مثال: x ← السرعة، ثم اختر الخط المطلوب.
                </p>
                <button
                  type="button"
                  onClick={addRow}
                  className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--journal-accent-strong)] px-4 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <Plus aria-hidden className="h-4 w-4" />
                  إضافة رمز
                </button>
              </div>
            ) : (
              <>
                {rows.map((row, index) => {
                  const serializedPreview = showTechnicalPreview
                    ? serializeMappingTarget(
                        row.arabic,
                        row.fontId,
                        row.legacySerialized,
                      )
                    : "";

                  return (
                    <div
                      key={row.id}
                      className="mapping-row-enter group rounded-xl border border-[var(--journal-border)] bg-white p-3 shadow-sm transition hover:border-[var(--journal-accent)] hover:shadow-md sm:p-4"
                    >
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-slate-100 px-2 text-xs font-bold text-slate-500">
                          {formatDigits(String(index + 1))}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeRow(index)}
                          aria-label={`حذف الرمز ${formatDigits(String(index + 1))}`}
                          title="حذف الرمز"
                          className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 transition hover:border-red-300 hover:bg-red-100"
                        >
                          <Trash2 aria-hidden className="h-4 w-4" />
                          <span>حذف</span>
                        </button>
                      </div>

                      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1.25fr)] sm:items-end">
                        <label className="block min-w-0">
                          <span className="mb-1 block text-xs font-semibold text-slate-500">
                            الرمز الأصلي
                          </span>
                          <div className="flex gap-2">
                            <input
                              id={`${row.id}-original`}
                              dir="ltr"
                              value={row.english}
                              onChange={(event) =>
                                updateRow(index, { english: event.target.value })
                              }
                              maxLength={128}
                              placeholder="x"
                              aria-label={`الرمز الأصلي ${index + 1}`}
                              className="min-h-10 min-w-0 flex-1 rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 font-mono text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
                            />
                            <CopyButton
                              value={row.english.trim()}
                              ariaLabel="نسخ الرمز الأصلي"
                              className="h-10 w-10 rounded-lg"
                            />
                          </div>
                        </label>

                        <ArrowLeftRight
                          aria-hidden
                          className="mb-3 hidden h-4 w-4 text-slate-400 sm:block"
                        />

                        <label className="block min-w-0">
                          <span className="mb-1 block text-xs font-semibold text-slate-500">
                            القيمة العربية
                          </span>
                          <div className="flex gap-2">
                            <input
                              dir="rtl"
                              value={row.arabic}
                              onChange={(event) => updateTarget(index, event.target.value)}
                              maxLength={128}
                              placeholder="السرعة"
                              aria-label={`القيمة العربية ${index + 1}`}
                              className="min-h-10 min-w-0 flex-1 rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 text-lg text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
                            />
                            <CopyButton
                              value={row.arabic.trim()}
                              ariaLabel="نسخ القيمة العربية"
                              className="h-10 w-10 rounded-lg"
                            />
                          </div>
                        </label>
                      </div>

                      <div
                        className={`mt-3 grid gap-3 md:items-start ${
                          showTechnicalPreview
                            ? "md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)]"
                            : "md:max-w-sm"
                        }`}
                      >
                        <div className="min-w-0">
                          <span className="mb-1 block text-xs font-semibold text-slate-500">
                            الخط
                          </span>
                          <MappingFontSelector
                            id={`${row.id}-font`}
                            value={row.fontId}
                            onChange={(fontId) => updateFont(index, fontId)}
                            ariaLabel={`خط الرمز ${index + 1}`}
                          />
                        </div>

                        {showTechnicalPreview ? (
                          <details className="rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2 text-xs text-slate-600">
                            <summary className="cursor-pointer font-semibold text-slate-600">
                              معاينة الصيغة التقنية
                            </summary>
                            <div className="mt-2 flex items-center gap-2" dir="ltr">
                              <code className="min-w-0 flex-1 overflow-x-auto rounded bg-white px-2 py-1.5 text-[11px] text-slate-700">
                                {serializedPreview || "—"}
                              </code>
                              <CopyButton
                                value={serializedPreview}
                                ariaLabel="نسخ الصيغة التقنية"
                                className="h-8 w-8 rounded-md"
                              />
                            </div>
                          </details>
                        ) : null}
                      </div>
                    </div>
                  );
                })}

                <div className="pt-2 text-center sm:text-start">
                  <button
                    type="button"
                    onClick={() => {
                      setRows([]);
                      setSaved(false);
                    }}
                    className="min-h-10 rounded-lg px-3 text-sm font-semibold text-red-700 transition hover:bg-red-50"
                  >
                    مسح جميع الرموز
                  </button>
                </div>
              </>
            )}
          </div>
        </section>
      </div>

      <footer className="flex shrink-0 justify-end border-t border-[var(--journal-border)] bg-white/95 px-4 py-3 sm:px-5 md:px-6">
        <button
          type="button"
          onClick={() => void save()}
          disabled={saving || rows === null}
          className="min-h-11 w-full rounded-lg bg-[var(--journal-accent-strong)] px-5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 sm:w-auto sm:min-w-36"
        >
          {saving ? "جارٍ الحفظ…" : "حفظ الرموز"}
        </button>
      </footer>
    </AnimatedOverlay>
  );
}
