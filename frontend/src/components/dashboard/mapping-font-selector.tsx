"use client";

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
  const selected = MAPPING_FONTS.find((font) => font.id === value);
  const selectedPreviewClass = previewClassName(value);

  return (
    <div className="min-w-0">
      <select
        id={id}
        value={value}
        onChange={(event) =>
          onChange(event.target.value as EditableMappingFontId)
        }
        aria-label={ariaLabel}
        className={`min-h-10 w-full rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)] ${selectedPreviewClass ?? ""}`}
      >
        {value === "custom" ? (
          <option value="custom">تنسيق مخصص محفوظ</option>
        ) : null}
        {MAPPING_FONTS.map((font) => (
          <option
            key={font.id}
            value={font.id}
            className={previewClassName(font.id)}
          >
            {font.labelAr}
          </option>
        ))}
      </select>

      {value === "custom" ? (
        <p className="mt-1.5 text-xs leading-5 text-amber-700">
          هذه صيغة قديمة أو مخصصة. ستبقى محفوظة كما هي ما لم تغيّر القيمة أو الخط.
        </p>
      ) : selected ? (
        <div className="mt-1.5 flex min-w-0 items-center justify-between gap-2">
          <p className="min-w-0 text-xs leading-5 text-slate-500">
            {selected.descriptionAr}
          </p>
          {selected.id !== "none" ? (
            <span
              aria-hidden
              className={`shrink-0 rounded-md border border-[var(--journal-border)] bg-white px-2 py-1 text-lg leading-none text-slate-800 ${selectedPreviewClass ?? ""}`}
              title={`معاينة ${selected.labelAr}`}
            >
              أبجد هوز
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
