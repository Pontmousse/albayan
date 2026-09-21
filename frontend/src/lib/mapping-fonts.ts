export const MAPPING_FONT_IDS = [
  "default",
  "takween",
  "diwani",
  "diwaniOutline",
  "maghribi",
] as const;

export type MappingFontId = (typeof MAPPING_FONT_IDS)[number];
export type EditableMappingFontId = MappingFontId | "custom";

export type MappingFontConfig = {
  id: MappingFontId;
  labelAr: string;
  descriptionAr: string;
  latexCommand: string | null;
  mode: "plain" | "command";
};

/**
 * Author-facing mapping styles.
 *
 * "default" deliberately means no special font command. The UI should not
 * expose a second "no font" choice: choosing no special font is exactly the
 * default state.
 */
export const MAPPING_FONTS: readonly MappingFontConfig[] = [
  {
    id: "default",
    labelAr: "الافتراضي",
    descriptionAr: "بدون خط خاص؛ تظهر القيمة بالخط الافتراضي للمعادلة.",
    latexCommand: null,
    mode: "plain",
  },
  {
    id: "takween",
    labelAr: "تكوين",
    descriptionAr: "يعرض القيمة بخط تكوين.",
    latexCommand: "butextakween",
    mode: "command",
  },
  {
    id: "diwani",
    labelAr: "ديواني",
    descriptionAr: "يعرض القيمة بالخط الديواني.",
    latexCommand: "butexdiwani",
    mode: "command",
  },
  {
    id: "diwaniOutline",
    labelAr: "ديواني مزخرف",
    descriptionAr: "يعرض القيمة بالديواني المزخرف.",
    latexCommand: "butexdiwanioutline",
    mode: "command",
  },
  {
    id: "maghribi",
    labelAr: "مغربي",
    descriptionAr: "يعرض القيمة بالخط المغربي.",
    latexCommand: "butexmaghribi",
    mode: "command",
  },
] as const;

export type ParsedMappingTarget = {
  target: string;
  fontId: EditableMappingFontId;
  /**
   * Exact older/custom serialization to keep untouched until the author edits
   * this row or explicitly chooses a supported style.
   */
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
 * Current authoring contract:
 * - default        -> raw/plain value (no special font command)
 * - takween        -> \\butextakween{...}
 * - diwani         -> \\butexdiwani{...}
 * - diwani outline -> \\butexdiwanioutline{...}
 * - maghribi       -> \\butexmaghribi{...}
 *
 * A recognized older default wrapper may carry legacySerialized so opening
 * and saving an unrelated row does not rewrite historical data silently. As
 * soon as that row is edited, callers clear legacySerialized and the current
 * plain default representation is emitted.
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
  if (!font || font.mode === "plain") {
    return legacySerialized ?? normalizedTarget;
  }
  if (font.latexCommand) {
    return `\\${font.latexCommand}{${normalizedTarget}}`;
  }
  return normalizedTarget;
}

/**
 * Decode a persisted mapping value back into author-facing state.
 * Unknown commands remain lossless in a custom state.
 *
 * Older default `\\text{...}` values are displayed as the single default
 * choice while retaining their exact serialized value until the author edits
 * that row. Old Jissr-style Diwani aliases remain readable as well.
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
    return {
      target: textTarget,
      fontId: "default",
      legacySerialized: serialized,
    };
  }

  if (looksLikeUnsupportedLatex(normalized)) {
    return {
      target: serialized,
      fontId: "custom",
      legacySerialized: serialized,
    };
  }

  return { target: normalized, fontId: "default" };
}

export function mappingFontLabel(fontId: EditableMappingFontId): string {
  if (fontId === "custom") return "تنسيق مخصص محفوظ";
  return MAPPING_FONTS.find((font) => font.id === fontId)?.labelAr ?? fontId;
}
