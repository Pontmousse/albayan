import { UserFacingError } from "@/lib/user-facing-errors";
import {
  parseMappingTarget,
  serializeMappingTarget,
  type EditableMappingFontId,
} from "@/lib/mapping-fonts";

export type EquationMappingRow = {
  english: string;
  arabic: string;
  fontId: EditableMappingFontId;
  legacySerialized?: string;
};

const MAX_MAPPING_LENGTH = 128;
const MAX_MAPPING_COUNT = 256;

export function equationMappingRows(
  mappings: Record<string, string>,
): EquationMappingRow[] {
  return Object.entries(mappings).map(([english, serialized]) => {
    const parsed = parseMappingTarget(serialized);
    return {
      english,
      arabic: parsed.target,
      fontId: parsed.fontId,
      legacySerialized: parsed.legacySerialized,
    };
  });
}

export function equationMappingsFromRows(
  rows: EquationMappingRow[],
): Record<string, string> {
  if (rows.length > MAX_MAPPING_COUNT) {
    throw new UserFacingError(`يمكن حفظ ${MAX_MAPPING_COUNT} رمزاً كحد أقصى.`);
  }

  const mappings: Record<string, string> = {};
  for (const row of rows) {
    const english = row.english.trim();
    const arabic = row.arabic.trim();

    if (!english && !arabic) continue;
    if (!english || !arabic) {
      throw new UserFacingError(
        "أكمل الرمز الأصلي ومقابله العربي، أو احذف الصف الفارغ.",
      );
    }
    if (english.length > MAX_MAPPING_LENGTH || arabic.length > MAX_MAPPING_LENGTH) {
      throw new UserFacingError(
        `يجب ألا يتجاوز كل رمز ${MAX_MAPPING_LENGTH} محرفاً.`,
      );
    }
    if (Object.prototype.hasOwnProperty.call(mappings, english)) {
      throw new UserFacingError(`الرمز الأصلي «${english}» مكرر.`);
    }

    mappings[english] = serializeMappingTarget(
      arabic,
      row.fontId,
      row.legacySerialized,
    );
  }
  return mappings;
}
