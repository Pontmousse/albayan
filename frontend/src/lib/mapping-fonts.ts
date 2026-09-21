export const MAPPING_FONT_IDS = ["default", "diwani", "none"] as const;

export type MappingFontId = (typeof MAPPING_FONT_IDS)[number];
export type EditableMappingFontId = MappingFontId | "custom";

export type MappingFontConfig = {
  id: MappingFontId;
  labelAr: string;
  descriptionAr: string;
  latexCommand: string | null;
};

export const MAPPING_FONTS: readonly MappingFontConfig[] = [
  {
    id: "default",
    labelAr: "النص الافتراضي",
    descriptionAr: "يُحفظ كنص عربي داخل المعادلة.",
    latexCommand: null,
  },
  {
    id: "diwani",
    labelAr: "الديواني",
    descriptionAr: "يستخدم تنسيق الديواني المدعوم في BuTeX.",
    latexCommand: "diwani",
  },
  {
    id: "none",
    labelAr: "بدون تنسيق",
    descriptionAr: "يحفظ القيمة كما هي من دون تغليف نصي.",
    latexCommand: null,
  },
] as const;

export type ParsedMappingTarget = {
  target: string;
  fontId: EditableMappingFontId;
  legacySerialized?: string;
};

const TEXT_PREFIX = "\\text{";
const DIWANI_PREFIX = "\\text{\\diwani{";

function hasOuterWrapper(value: string, prefix: string, suffix: string) {
  return value.startsWith(prefix) && value.endsWith(suffix);
}

function looksLikeUnsupportedLatex(value: string) {
  return /^\\[A-Za-z@]+(?:\{|\[|\s|$)/.test(value);
}

/**
 * Convert the author-facing target + style into the mapping value persisted by
 * the existing article equation-mappings API.
 *
 * The contract mirrors the currently supported Jissr/BuTeX forms:
 * - default -> \\text{...}
 * - diwani  -> \\text{\\diwani{...}}
 * - none    -> raw value
 */
export function serializeMappingTarget(
  target: string,
  fontId: EditableMappingFontId,
  legacySerialized?: string,
): string {
  const normalizedTarget = target.trim();

  if (fontId === "custom") {
    return legacySerialized ?? normalizedTarget;
  }
  if (fontId === "none") {
    return normalizedTarget;
  }
  if (fontId === "diwani") {
    return `\\text{\\diwani{${normalizedTarget}}}`;
  }
  return `\\text{${normalizedTarget}}`;
}

/**
 * Decode a persisted mapping value back into author-facing state.
 * Unknown LaTeX commands are deliberately kept lossless in a custom state.
 */
export function parseMappingTarget(serialized: string): ParsedMappingTarget {
  const normalized = serialized.trim();

  if (hasOuterWrapper(normalized, DIWANI_PREFIX, "}}")) {
    return {
      target: normalized.slice(DIWANI_PREFIX.length, -2),
      fontId: "diwani",
    };
  }

  if (hasOuterWrapper(normalized, TEXT_PREFIX, "}")) {
    const inner = normalized.slice(TEXT_PREFIX.length, -1);
    if (looksLikeUnsupportedLatex(inner)) {
      return {
        target: normalized,
        fontId: "custom",
        legacySerialized: normalized,
      };
    }
    return { target: inner, fontId: "default" };
  }

  if (looksLikeUnsupportedLatex(normalized)) {
    return {
      target: normalized,
      fontId: "custom",
      legacySerialized: normalized,
    };
  }

  return { target: normalized, fontId: "none" };
}

export function mappingFontLabel(fontId: EditableMappingFontId): string {
  if (fontId === "custom") return "تنسيق مخصص محفوظ";
  return MAPPING_FONTS.find((font) => font.id === fontId)?.labelAr ?? fontId;
}
