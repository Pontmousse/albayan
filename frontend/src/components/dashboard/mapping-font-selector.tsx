"use client";

import {
  MAPPING_FONTS,
  type EditableMappingFontId,
} from "@/lib/mapping-fonts";
import {
  ResponsiveSelect,
  type ResponsiveSelectOption,
} from "@/components/ui/responsive-select";

import styles from "./mapping-font-selector.module.css";

function previewClassName(fontId: EditableMappingFontId): string | undefined {
  if (fontId === "takween") return styles.takween;
  if (fontId === "diwani") return styles.diwani;
  if (fontId === "diwaniOutline") return styles.diwaniOutline;
  if (fontId === "maghribi") return styles.maghribi;
  return undefined;
}

export function MappingFontSelector({
  value,
  onChange,
}: {
  value: EditableMappingFontId;
  onChange: (value: EditableMappingFontId) => void;
}) {
  const selected = MAPPING_FONTS.find((font) => font.id === value);
  const options: readonly ResponsiveSelectOption<EditableMappingFontId>[] = [
    ...(value === "custom"
      ? [
          {
            value: "custom" as const,
            label: "تنسيق محفوظ",
            description: "قيمة قديمة أو مخصصة محفوظة كما هي.",
          },
        ]
      : []),
    ...MAPPING_FONTS.map((font) => ({
      value: font.id,
      label: font.labelAr,
      description: font.descriptionAr,
      separatorBefore: font.id === "none",
    })),
  ];

  function visualSample(fontId: EditableMappingFontId) {
    return fontId === "none" ? "كما كُتبت" : "أبجد هوز";
  }

  return (
    <div className="min-w-0">
      <ResponsiveSelect
        label="الخط"
        value={value}
        options={options}
        onChange={onChange}
        renderSelected={(option) => (
          <span className="flex min-w-0 items-center justify-between gap-3">
            <span className="truncate font-semibold">{option.label}</span>
            {option.value !== "custom" ? (
              <span
                aria-hidden
                className={`shrink-0 text-lg leading-none ${previewClassName(option.value) ?? ""}`}
              >
                {visualSample(option.value)}
              </span>
            ) : null}
          </span>
        )}
        renderOption={(option, { mobile }) => (
          <span className="flex min-w-0 items-center justify-between gap-4">
            <span className="min-w-0">
              <span
                className={`block ${mobile ? "text-base font-semibold" : "text-sm font-semibold"}`}
              >
                {option.label}
              </span>
              {option.description ? (
                <span
                  className={`mt-0.5 block leading-relaxed text-slate-500 ${mobile ? "text-sm" : "text-xs"}`}
                >
                  {option.description}
                </span>
              ) : null}
            </span>
            {option.value !== "custom" ? (
              <span
                aria-hidden
                className={`shrink-0 rounded-md border border-[var(--journal-border)] bg-white px-2 py-1 text-xl leading-none text-slate-800 ${previewClassName(option.value) ?? ""}`}
              >
                {visualSample(option.value)}
              </span>
            ) : null}
          </span>
        )}
      />

      {value === "custom" ? (
        <p className="mt-1.5 text-xs leading-5 text-amber-700">
          هذا تنسيق قديم أو مخصص، وسيبقى محفوظاً كما هو ما لم تغيّر القيمة أو الخط.
        </p>
      ) : selected ? (
        <div className="mt-1.5 min-w-0">
          <p
            className={`min-w-0 text-xs leading-5 ${selected.id === "none" ? "font-medium text-amber-700" : "text-slate-500"}`}
          >
            {selected.descriptionAr}
          </p>
        </div>
      ) : null}
    </div>
  );
}
