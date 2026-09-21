export const MAPPING_FONT_IDS = ["default", "diwani", "none"] as const;

export type MappingFontId = (typeof MAPPING_FONT_IDS)[number];
export type EditableMappingFontId = MappingFontId | "custom";

export type MappingFontConfig = {
  id: MappingFontId;
  labelAr: string;
  descriptionAr: string;
  latexCommand: string | null;
  mode: "text" | "command" | "raw";
};

export const MAPPING_FONTS: readonly MappingFontConfig[] = [
  {
    id: "default",
    labelAr: "النص الافتراضي",
    descriptionAr: "يُحفظ كنص عربي داخل المعادلة.",
    latexCommand: null,
    mode: "text",
  },
  {
    id: "diwani",
    labelAr: "الديواني",
    descriptionAr: "يستخدم تنسيق الديواني المدعوم في BuTeX.",
    latexCommand: "diwani",
    mode: "command",
  },
  {
    id: "none",
    labelAr: "بدون تنسيق",
    descriptionAr: "يحفظ القيمة كما هي من دون تغليف نصي.",
    latexCommand: null,
    mode: "raw",
  },
] as const;

export type ParsedMappingTarget = {
  target: string;
  fontId: EditableMappingFontId;
  legacySerialized?: string;
};

const TEXT_PREFIX = "\\text{";

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
 * Current verified Jissr/BuTeX contract:
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

  const font = MAPPING_FONTS.find((candidate) => candidate.id === fontId);
  if (!font || font.mode === "text") {
    return `\\text{${normalizedTarget}}`;
  }
  if (font.mode === "raw") {
    return normalizedTarget;
  }
  if (font.latexCommand) {
    return `\\text{\\${font.latexCommand}{${normalizedTarget}}}`;
  }
  return `\\text{${normalizedTarget}}`;
}

/**
 * Decode a persisted mapping value back into author-facing state.
 * Unknown LaTeX commands are deliberately kept lossless in a custom state.
 */
export function parseMappingTarget(serialized: string): ParsedMappingTarget {
  const normalized = serialized.trim();

  for (const font of MAPPING_FONTS) {
    if (font.mode !== "command" || !font.latexCommand) continue;
    const prefix = `\\text{\\${font.latexCommand}{`;
    if (hasOuterWrapper(normalized, prefix, "}}")) {
      return {
        target: normalized.slice(prefix.length, -2),
        fontId: font.id,
      };
    }
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
