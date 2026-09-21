"use client";

import {
  MAPPING_FONTS,
  type EditableMappingFontId,
} from "@/lib/mapping-fonts";

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

  return (
    <div className="min-w-0">
      <select
        id={id}
        value={value}
        onChange={(event) =>
          onChange(event.target.value as EditableMappingFontId)
        }
        aria-label={ariaLabel}
        className="min-h-10 w-full rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
      >
        {value === "custom" ? (
          <option value="custom">تنسيق مخصص محفوظ</option>
        ) : null}
        {MAPPING_FONTS.map((font) => (
          <option key={font.id} value={font.id}>
            {font.labelAr}
          </option>
        ))}
      </select>
      {value === "custom" ? (
        <p className="mt-1.5 text-xs leading-5 text-amber-700">
          هذه صيغة قديمة أو مخصصة. ستبقى محفوظة كما هي ما لم تغيّر القيمة أو الخط.
        </p>
      ) : selected ? (
        <p className="mt-1.5 text-xs leading-5 text-slate-500">
          {selected.descriptionAr}
        </p>
      ) : null}
    </div>
  );
}
