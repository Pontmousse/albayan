export type EditorialMember = {
  name: string;
  role: string;
  affiliation: string;
};

/**
 * أعضاء هيئة التحرير المعلَنون. لا تُدرَج أسماء لم تُعتمد بعد.
 */
export const editorialMembers: EditorialMember[] = [
  {
    name: "الغالي عصري",
    role: "رئيس التحرير",
    affiliation:
      "طالب دكتوراه في جامعة يورك بكندا، خريج جامعة الحسن الثاني بالدار البيضاء، المغرب",
  },
];
