export type DashboardRole = "author" | "reviewer" | "admin";

export type DashboardSection = {
  id: string;
  label: string;
  href: string;
  roles: DashboardRole[];
};

export const dashboardSections: DashboardSection[] = [
  { id: "overview", label: "نظرة عامة", href: "/maktabi", roles: ["author"] },
  { id: "articles", label: "مقالاتي", href: "/maktabi/maqalati", roles: ["author"] },
  // لاحقاً: { id: "reviews", label: "مراجعاتي", href: "/maktabi/murajaati", roles: ["reviewer"] }
];

// v1: كل مستخدم مسجّل يُعامل كمؤلف — تتوسع لاحقاً عبر API
export const currentRoles: DashboardRole[] = ["author"];

export function visibleSections(roles: DashboardRole[] = currentRoles) {
  return dashboardSections.filter((section) =>
    section.roles.some((role) => roles.includes(role)),
  );
}
