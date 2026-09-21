export type EquationMappingRow = {
  english: string;
  arabic: string;
};

const MAX_MAPPING_LENGTH = 128;
const MAX_MAPPING_COUNT = 256;

export function equationMappingRows(
  mappings: Record<string, string>,
): EquationMappingRow[] {
  return Object.entries(mappings).map(([english, arabic]) => ({ english, arabic }));
}

export function equationMappingsFromRows(
  rows: EquationMappingRow[],
): Record<string, string> {
  if (rows.length > MAX_MAPPING_COUNT) {
    throw new Error(`يمكن حفظ ${MAX_MAPPING_COUNT} رمزاً كحد أقصى.`);
  }

  const mappings: Record<string, string> = {};
  for (const row of rows) {
    const english = row.english.trim();
    const arabic = row.arabic.trim();

    if (!english && !arabic) continue;
    if (!english || !arabic) {
      throw new Error("أكمل الرمز الأصلي والرمز العربي، أو احذف الصف الفارغ.");
    }
    if (english.length > MAX_MAPPING_LENGTH || arabic.length > MAX_MAPPING_LENGTH) {
      throw new Error(`يجب ألا يتجاوز كل رمز ${MAX_MAPPING_LENGTH} محرفاً.`);
    }
    if (Object.prototype.hasOwnProperty.call(mappings, english)) {
      throw new Error(`الرمز الأصلي «${english}» مكرر.`);
    }
    mappings[english] = arabic;
  }
  return mappings;
}
