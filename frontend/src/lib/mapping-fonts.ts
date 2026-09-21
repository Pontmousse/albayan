export const MAPPING_FONT_IDS = [
  "default",
  "takween",
  "diwani",
  "diwaniOutline",
  "maghribi",
  "none",
] as const;

export type MappingFontId = (typeof MAPPING_FONT_IDS)[number];
export type EditableMappingFontId = MappingFontId | "custom";

export type MappingFontConfig = {
  id: MappingFontId;
  labelAr: string;
  descriptionAr: string;
  latexCommand: string | null;
  mode: "text" | "command" | "raw";
};

/**
 * Author-facing mapping styles supported by BuTeX v7.1.0.
 *
 * Keep the canonical BuTeX command names here. The UI never asks authors to
 * type these commands; this table is the single serialization source of truth.
 */
export const MAPPING_FONTS: readonly MappingFontConfig[] = [
  {
    id: "default",
    labelAr: "الافتراضي — نص عربي",
    descriptionAr: "الخيار المعتاد للنص العربي داخل المعادلة.",
    latexCommand: null,
    mode: "text",
  },
  {
    id: "takween",
    labelAr: "تكوين",
    descriptionAr: "صياغة عربية بخط تكوين.",
    latexCommand: "butextakween",
    mode: "command",
  },
  {
    id: "diwani",
    labelAr: "ديواني",
    descriptionAr: "صياغة عربية بالخط الديواني.",
    latexCommand: "butexdiwani",
    mode: "command",
  },
  {
    id: "diwaniOutline",
    labelAr: "ديواني مزخرف",
    descriptionAr: "صياغة ديوانية مزخرفة بإطار.",
    latexCommand: "butexdiwanioutline",
    mode: "command",
  },
  {
    id: "maghribi",
    labelAr: "مغربي",
    descriptionAr: "صياغة عربية بالخط المغربي.",
    latexCommand: "butexmaghribi",
    mode: "command",
  },
  {
    id: "none",
    labelAr: "كما كُتبت (متقدم)",
    descriptionAr: "يبقي القيمة كما كُتبت من دون تطبيق نمط النص العربي المعتاد.",
    latexCommand: null,
    mode: "raw",
  },
] as const;

export type ParsedMappingTarget = {
  target: string;
  fontId: EditableMappingFontId;
  legacySerialized?: string;
};

function looksLikeUnsupportedLatex(value: string) {
  return /^\\[A-Za-z@]+(?:\{|\[|\s|$)/.test(value);
}

/**
 * Return the contents of an exact single-argument command while respecting
 * nested and escaped braces. Trailing content means the value is not an exact
 * wrapper and is therefore left untouched.
 */
function unwrapCommand(value: string, command: string): string | null {
  const prefix = `\\${command}{`;
  if (!value.startsWith(prefix)) return null;

  let depth = 1;
  let escaped = false;
  for (let index = prefix.length; index < value.length; index += 1) {
    const character = value[index];

    if (escaped) {
      escaped = false;
      continue;
    }
    if (character === "\\") {
      escaped = true;
      continue;
    }
    if (character === "{") {
      depth += 1;
      continue;
    }
    if (character === "}") {
      depth -= 1;
      if (depth === 0) {
        if (index !== value.length - 1) return null;
        return value.slice(prefix.length, index);
      }
    }
  }

  return null;
}

/**
 * Convert the author-facing target + style into the value persisted by the
 * existing article equation-mappings API.
 *
 * BuTeX v7.1.0 canonical contract:
 * - default        -> \\text{...}
 * - takween        -> \\butextakween{...}
 * - diwani         -> \\butexdiwani{...}
 * - diwani outline -> \\butexdiwanioutline{...}
 * - maghribi       -> \\butexmaghribi{...}
 * - none           -> raw value
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
    return `\\${font.latexCommand}{${normalizedTarget}}`;
  }
  return `\\text{${normalizedTarget}}`;
}

/**
 * Decode a persisted mapping value back into author-facing state.
 * Unknown LaTeX commands are deliberately kept lossless in a custom state.
 *
 * The old Jissr-style \\text{\\diwani{...}} / \\diwani{...} forms remain
 * readable so existing values can be edited without data loss. New saves use
 * the canonical BuTeX command above once the author explicitly changes style.
 */
export function parseMappingTarget(serialized: string): ParsedMappingTarget {
  const normalized = serialized.trim();

  for (const font of MAPPING_FONTS) {
    if (font.mode !== "command" || !font.latexCommand) continue;
    const target = unwrapCommand(normalized, font.latexCommand);
    if (target !== null) {
      return { target, fontId: font.id };
    }
  }

  // Backwards compatibility with the earlier Jissr-inspired AlBayan/Jissr
  // representation. Never emit these aliases for new values.
  const directLegacyDiwani = unwrapCommand(normalized, "diwani");
  if (directLegacyDiwani !== null) {
    return { target: directLegacyDiwani, fontId: "diwani" };
  }

  const textTarget = unwrapCommand(normalized, "text");
  if (textTarget !== null) {
    const nestedLegacyDiwani = unwrapCommand(textTarget, "diwani");
    if (nestedLegacyDiwani !== null) {
      return { target: nestedLegacyDiwani, fontId: "diwani" };
    }
    if (looksLikeUnsupportedLatex(textTarget)) {
      return {
        target: serialized,
        fontId: "custom",
        legacySerialized: serialized,
      };
    }
    return { target: textTarget, fontId: "default" };
  }

  if (looksLikeUnsupportedLatex(normalized)) {
    return {
      target: serialized,
      fontId: "custom",
      legacySerialized: serialized,
    };
  }

  return { target: normalized, fontId: "none" };
}

export function mappingFontLabel(fontId: EditableMappingFontId): string {
  if (fontId === "custom") return "تنسيق محفوظ";
  return MAPPING_FONTS.find((font) => font.id === fontId)?.labelAr ?? fontId;
}
